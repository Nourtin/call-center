import pandas as pd
import io
import requests
import gspread
import re
import json

def list_sheets(sheet_url):
    """
    Retourne le fichier en mémoire et la liste des feuilles
    """
    base_url = sheet_url.split("/edit")[0].split("/pub")[0]
    export_url = base_url + "/export?format=xlsx"

    response = requests.get(export_url, timeout=500)
    response.raise_for_status()
    fichier = io.BytesIO(response.content)

    xls = pd.ExcelFile(fichier)
    sheets = xls.sheet_names

    return fichier, sheets


def choisir_feuille(fichier, sheet_name):
    """
    Lire une feuille spécifique depuis le fichier déjà téléchargé
    """
    fichier.seek(0)
    df = pd.read_excel(fichier, sheet_name=sheet_name)
    return df


def get_sheet_id_from_url(sheet_url):
    """
    Extrait l'ID du Google Sheet depuis l'URL
    """
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
    if not match:
        raise ValueError("Impossible d'extraire l'ID du Google Sheet depuis l'URL")
    return match.group(1)


def get_gid_from_url(sheet_url):
    """
    Extrait le gid (ID de feuille) depuis l'URL si présent
    """
    match = re.search(r'gid=(\d+)', sheet_url)
    if match:
        return match.group(1)
    return None


def ecrire_formules_direct_api(sheet_url, feuille_nom, url_classification, url_archive, ligne_debut=2):
    """
    Écrit directement dans Google Sheets en utilisant l'API avec un sheet public éditable
    """
    try:
        sheet_id = get_sheet_id_from_url(sheet_url)
        
        # Utiliser l'API Google Sheets directement avec requests
        # URL de base pour l'API
        base_api_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        
        # D'abord, obtenir les informations de la feuille pour trouver le sheetId
        response = requests.get(
            base_api_url,
            params={'fields': 'sheets.properties'},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"✗ Erreur API: {response.status_code}")
            print(f"  {response.text}")
            return False
        
        data = response.json()
        
        # Trouver le sheetId correspondant au nom de la feuille
        sheet_gid = None
        for sheet in data.get('sheets', []):
            if sheet['properties']['title'] == feuille_nom:
                sheet_gid = sheet['properties']['sheetId']
                break
        
        if sheet_gid is None:
            print(f"✗ Feuille '{feuille_nom}' non trouvée")
            return False
        
        print(f"✓ Feuille trouvée: {feuille_nom} (sheetId: {sheet_gid})")
        
        # Obtenir les valeurs actuelles pour déterminer le nombre de lignes
        range_name = f"'{feuille_nom}'!A1:AH"
        values_response = requests.get(
            f"{base_api_url}/values/{range_name}",
            timeout=30
        )
        
        nb_lignes = 0
        if values_response.status_code == 200:
            values_data = values_response.json()
            nb_lignes = len(values_data.get('values', []))
            print(f"✓ {nb_lignes} lignes trouvées")
        
        if nb_lignes == 0:
            nb_lignes = 1000  # Valeur par défaut
            print(f"⚠ Nombre de lignes non détecté, utilisation de {nb_lignes}")
        
        # Préparer les formules
        formule_AG = f'=IFERROR(INDEX(IMPORTRANGE("{url_classification}";"Classification Leads!AC:AC");ROW());IFERROR(INDEX(IMPORTRANGE("{url_archive}";"ARCHIVE CLASSIFICATION!AC:AC");ROW());"Non trouvé"))'
        
        formule_AH_base = f'=IFERROR(INDEX(IMPORTRANGE("{url_classification}";"LEAD DATA!R:R");ROW());IFERROR(INDEX(IMPORTRANGE("{url_classification}";"LEAD BOT PI!E:E");MATCH(SUBSTITUTE(AA2;" ";"");ARRAYFORMULA(SUBSTITUTE(IMPORTRANGE("{url_classification}";"LEAD BOT PI!AI:AI");" ";""));0));"Non trouvé"))'
        
        # Préparer les valeurs pour l'API batchUpdate
        requests_batch = []
        
        for ligne in range(ligne_debut, nb_lignes + 1):
            # Formule AG
            requests_batch.append({
                'updateCells': {
                    'range': {
                        'sheetId': sheet_gid,
                        'startRowIndex': ligne - 1,
                        'endRowIndex': ligne,
                        'startColumnIndex': 32,  # AG = colonne 33 (0-indexed)
                        'endColumnIndex': 33
                    },
                    'rows': [{
                        'values': [{
                            'userEnteredValue': {
                                'formulaValue': formule_AG
                            }
                        }]
                    }],
                    'fields': 'userEnteredValue'
                }
            })
            
            # Formule AH
            formule_AH = formule_AH_base.replace('AA2', f'AA{ligne}')
            requests_batch.append({
                'updateCells': {
                    'range': {
                        'sheetId': sheet_gid,
                        'startRowIndex': ligne - 1,
                        'endRowIndex': ligne,
                        'startColumnIndex': 33,  # AH = colonne 34 (0-indexed)
                        'endColumnIndex': 34
                    },
                    'rows': [{
                        'values': [{
                            'userEnteredValue': {
                                'formulaValue': formule_AH
                            }
                        }]
                    }],
                    'fields': 'userEnteredValue'
                }
            })
            
            # Traiter par lots de 50 pour éviter les timeouts
            if len(requests_batch) >= 100:
                # Envoyer le batch
                batch_url = f"{base_api_url}:batchUpdate"
                batch_data = {'requests': requests_batch}
                
                batch_response = requests.post(
                    batch_url,
                    json=batch_data,
                    timeout=60
                )
                
                if batch_response.status_code != 200:
                    print(f"⚠ Erreur lors de l'envoi du batch: {batch_response.status_code}")
                
                requests_batch = []
                print(f"  Progression: ligne {ligne}/{nb_lignes}")
        
        # Envoyer le reste
        if requests_batch:
            batch_url = f"{base_api_url}:batchUpdate"
            batch_data = {'requests': requests_batch}
            
            batch_response = requests.post(
                batch_url,
                json=batch_data,
                timeout=60
            )
            
            if batch_response.status_code != 200:
                print(f"⚠ Erreur lors de l'envoi du dernier batch: {batch_response.status_code}")
        
        print(f"\n✓ Formules appliquées avec succès !")
        print(f"  - Colonne AG: {nb_lignes - ligne_debut + 1} cellules")
        print(f"  - Colonne AH: {nb_lignes - ligne_debut + 1} cellules")
        print(f"  - Formule AG: {formule_AG[:80]}...")
        print(f"  - Formule AH: {formule_AH_base[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def appliquer_formules_simple(sheet_url, feuille_nom, url_classification, url_archive, ligne_debut=2):
    """
    Version simplifiée utilisant gspread (peut avoir des problèmes avec None)
    """
    try:
        # Essayer avec gspread
        sheet_id = get_sheet_id_from_url(sheet_url)
        
        # Créer un client sans auth
        client = gspread.Client(None)
        
        # Pour éviter l'erreur NoneType, on modifie directement la session
        session = requests.Session()
        client.session = session
        
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(feuille_nom)
        
        # Obtenir le nombre de lignes
        all_values = worksheet.get_all_values()
        nb_lignes = len(all_values)
        
        print(f"✓ Connecté à la feuille '{feuille_nom}' ({nb_lignes} lignes)")
        
        # Formules
        formule_AG = f'=IFERROR(INDEX(IMPORTRANGE("{url_classification}";"Classification Leads!AC:AC");ROW());IFERROR(INDEX(IMPORTRANGE("{url_archive}";"ARCHIVE CLASSIFICATION!AC:AC");ROW());"Non trouvé"))'
        
        formule_AH_base = f'=IFERROR(INDEX(IMPORTRANGE("{url_classification}";"LEAD DATA!R:R");ROW());IFERROR(INDEX(IMPORTRANGE("{url_classification}";"LEAD BOT PI!E:E");MATCH(SUBSTITUTE(AA2;" ";"");ARRAYFORMULA(SUBSTITUTE(IMPORTRANGE("{url_classification}";"LEAD BOT PI!AI:AI");" ";""));0));"Non trouvé"))'
        
        # Mettre à jour cellule par cellule (plus lent mais plus fiable)
        for ligne in range(ligne_debut, nb_lignes + 1):
            try:
                # Formule AG
                worksheet.update_acell(f'AG{ligne}', formule_AG)
                
                # Formule AH
                formule_AH = formule_AH_base.replace('AA2', f'AA{ligne}')
                worksheet.update_acell(f'AH{ligne}', formule_AH)
                
                if ligne % 10 == 0:
                    print(f"  Progression: ligne {ligne}/{nb_lignes}")
                    
            except Exception as e:
                print(f"⚠ Erreur ligne {ligne}: {str(e)[:50]}")
        
        print(f"\n✓ Formules appliquées avec succès !")
        return True
        
    except Exception as e:
        print(f"✗ Erreur gspread: {str(e)}")
        print("\n⚠ Utilisation de la méthode alternative via l'API directe...")
        return ecrire_formules_direct_api(sheet_url, feuille_nom, url_classification, url_archive, ligne_debut)


def lancer_application_formules():
    """
    Interface interactive pour appliquer les formules
    """
    print("\n=== Application des formules AG et AH ===\n")
    
    # URL de la feuille principale
    sheet_url = input("1. URL de votre Google Sheet principal: ").strip()
    
    # Afficher les feuilles disponibles
    try:
        fichier, sheets = list_sheets(sheet_url)
        print(f"\n✓ Feuilles trouvées: {', '.join(sheets)}")
    except:
        print("⚠ Impossible de lister les feuilles, continuez...")
        sheets = []
    
    feuille_nom = input("2. Nom de la feuille où appliquer les formules: ").strip()
    
    # URLs d'importation
    print("\n3. URLs des feuilles sources:")
    url_classification = input("   URL pour 'Classification Leads' et 'LEAD DATA': ").strip()
    url_archive = input("   URL pour 'ARCHIVE CLASSIFICATION' (Entrée pour utiliser la même): ").strip()
    
    if not url_archive:
        url_archive = url_classification
    
    # Ligne de départ
    ligne_debut = input("4. Ligne de départ pour les formules (défaut: 2): ").strip()
    ligne_debut = int(ligne_debut) if ligne_debut else 2
    
    print(f"\n📋 Résumé:")
    print(f"  - Sheet principal: {sheet_url[:50]}...")
    print(f"  - Feuille: {feuille_nom}")
    print(f"  - Colonnes: AG et AH")
    print(f"  - À partir de la ligne: {ligne_debut}")
    
    confirmation = input("\n✓ Appliquer les formules? (o/n): ").strip().lower()
    
    if confirmation == 'o':
        print("\n🚀 Application en cours...\n")
        succes = appliquer_formules_simple(
            sheet_url, 
            feuille_nom, 
            url_classification, 
            url_archive, 
            ligne_debut
        )
        
        if succes:
            print("\n✅ Terminé ! Vérifiez votre Google Sheet.")
        else:
            print("\n❌ Échec de l'application des formules.")
            print("Vérifiez que le Google Sheet est bien en mode 'Anyone with the link can edit'")
    else:
        print("❌ Opération annulée.")


# Configuration directe
def appliquer_direct():
    """
    Version non-interactive avec vos URLs
    """
    # MODIFIER CES VALEURS
    SHEET_PRINCIPAL_URL = "https://docs.google.com/spreadsheets/d/VOTRE_ID/edit"
    FEUILLE_NOM = "Nom de votre feuille"
    URL_CLASSIFICATION = "https://docs.google.com/spreadsheets/d/ID_CLASSIFICATION/edit"
    URL_ARCHIVE = "https://docs.google.com/spreadsheets/d/ID_ARCHIVE/edit"  # ou même URL
    
    appliquer_formules_simple(
        SHEET_PRINCIPAL_URL,
        FEUILLE_NOM,
        URL_CLASSIFICATION,
        URL_ARCHIVE,
        ligne_debut=2
    )


if __name__ == "__main__":
    print("=== Google Sheets - Formules AG et AH ===\n")
    print("1. Mode interactif (recommandé)")
    print("2. Mode direct (URLs dans le code)")
    print("3. Tester la connexion")
    
    choix = input("\nVotre choix: ").strip()
    
    if choix == "1":
        lancer_application_formules()
    elif choix == "2":
        print("\n⚠ Vérifiez que les URLs sont correctes dans 'appliquer_direct()'")
        conf = input("Continuer? (o/n): ")
        if conf.lower() == 'o':
            appliquer_direct()
    elif choix == "3":
        url = input("URL du Google Sheet à tester: ")
        try:
            fichier, sheets = list_sheets(url)
            print(f"✓ Connexion réussie !")
            print(f"  Feuilles: {sheets}")
        except Exception as e:
            print(f"✗ Erreur: {e}")
    else:
        print("Choix invalide")