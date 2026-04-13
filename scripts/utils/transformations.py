"""Data transformation utilities."""
import pandas as pd

def build_row(c: dict, vars_dict: dict, unique_id: str, from_num: str) -> dict:
    """
    Reconstruit le dictionnaire row depuis les données brutes de l'API.
    Identique à ta logique existante.
    """
    return {
        "UniqueID":                    unique_id,
        "from_number":                 from_num,
        "agent_id":                    c.get("agent_id", ""),
        "Timestamp":                   c.get("start_time", ""),
        "Duration_seconds":            c.get("duration_seconds", 0),
        "callee_name":                 vars_dict.get("callee_name") or c.get("callee_name", ""),
        "Apellido":                    vars_dict.get("Apellido", ""),
        "Edad":                        vars_dict.get("Edad", ""),
        "direccion":                   vars_dict.get("direccion", ""),
        "Ciudad":                      vars_dict.get("Ciudad", ""),
        "codigo_postal":               vars_dict.get("codigo_postal", ""),
        "adress_origine":              vars_dict.get("adress_origine", ""),
        "code_postal":                 vars_dict.get("code_postal", ""),
        "tipo_vivienda":               vars_dict.get("tipo_vivienda", ""),
        "superfici_vivienda":          vars_dict.get("superfici_vivienda", ""),
        "superfici_desvan":            vars_dict.get("superfici_desvan", ""),
        "estado_desvan":               vars_dict.get("estado_desvan", ""),
        "accesso_desvan":              vars_dict.get("accesso_desvan", ""),
        "tiene_desvan":                vars_dict.get("tiene_desvan", ""),
        "calefaccion":                 vars_dict.get("calefaccion", ""),
        "suelo":                       vars_dict.get("suelo", ""),
        "altura":                      vars_dict.get("altura", ""),
        "piso_casa":                   vars_dict.get("piso_casa", ""),
        "proprietad":                  vars_dict.get("proprietad", ""),
        "disponibilidad_visita":       vars_dict.get("disponibilidad_visita", ""),
        "disponibilidad_llamada":      vars_dict.get("disponibilidad_llamada", ""),
        "debe_ser_llamado_de_nuevo":   vars_dict.get("debe_ser_llamado_de_nuevo", ""),
        "resumen_conversacion":        vars_dict.get("resumen_conversacion", ""),
        "other_extract":               vars_dict.get("other_extract", ""),
        "Messagerie":                  vars_dict.get("Messagerie", ""),
        "list_name":                   vars_dict.get("list_name") or c.get("list_name", ""),
        "url": f'="http://37.59.222.18/RECORDINGS/MP3/"&"{from_num}"&"-all.mp3"',
        "Classification":              "",
        "Resultat":                    ""
    }

def filter_calls(calls: list) -> list:
    """Supprime les appels de 0 seconde."""
    filtered = [c for c in calls if c.get("duration_seconds", 0) > 0]
    print(f"Filtre durée → {len(calls) - len(filtered)} supprimés | {len(filtered)} valides")
    return filtered