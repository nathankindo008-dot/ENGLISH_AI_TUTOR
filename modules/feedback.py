def extract_feedback(llm_response):
    """
    Extrait les corrections, vocabulaire et tips depuis la réponse de l'IA.

    Args:
        llm_response (str): La réponse brute de l'IA

    Returns:
        dict: {
            "response": str,        # La réponse conversationnelle
            "corrections": list,    # Liste des corrections
            "vocabulary": list,     # Liste des mots de vocabulaire
            "grammar_tips": list    # Liste des tips grammaticaux
        }
    """
    # Initialiser le dictionnaire de retour
    sections = {
        "response": "",
        "corrections": [],
        "vocabulary": [],
        "grammar_tips": []
    }

    # Séparer la réponse en lignes
    lines = llm_response.split("\n")
    
    # Variable pour tracker la section courante
    current_section = "response"
    
    # Parcourir chaque ligne
    for line in lines:
        line = line.strip()  # Enlever les espaces inutiles
        
        # Détecter les sections par leurs balises
        if "**Corrections:**" in line or "**Correction:**" in line:
            current_section = "corrections"
            # Extraire le contenu après la balise
            content = line.split("**Corrections:**")[-1].split("**Correction:**")[-1].strip()
            if content:
                sections["corrections"].append(content)
        
        elif "**Vocabulary:**" in line or "**Vocab:**" in line:
            current_section = "vocabulary"
            content = line.split("**Vocabulary:**")[-1].split("**Vocab:**")[-1].strip()
            if content:
                sections["vocabulary"].append(content)
        
        elif "**Grammar Tip:**" in line or "**Grammar:**" in line:
            current_section = "grammar_tips"
            content = line.split("**Grammar Tip:**")[-1].split("**Grammar:**")[-1].strip()
            if content:
                sections["grammar_tips"].append(content)
        
        else:
            # Ajouter le contenu à la section courante
            if line:  # Ignorer les lignes vides
                if current_section == "response":
                    sections["response"] += line + " "
                elif current_section == "corrections":
                    sections["corrections"].append(line)
                elif current_section == "vocabulary":
                    sections["vocabulary"].append(line)
                elif current_section == "grammar_tips":
                    sections["grammar_tips"].append(line)
    
    # Nettoyer la réponse (enlever les espaces en trop)
    sections["response"] = sections["response"].strip()
    
    return sections
