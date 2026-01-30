def extract_feedback(llm_response):
    """
    Extrait les corrections, vocabulaire et tips depuis la réponse de l'IA.
    """
    sections = {
        "response": "",
        "corrections": [],
        "vocabulary": [],
        "grammar_tips": []
    }

    lines = llm_response.split("\n")
    current_section = "response"
    
    for line in lines:
        line = line.strip()
        
        if "**Corrections:**" in line or "**Correction:**" in line:
            current_section = "corrections"
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
            if line:
                if current_section == "response":
                    sections["response"] += line + " "
                elif current_section == "corrections":
                    sections["corrections"].append(line)
                elif current_section == "vocabulary":
                    sections["vocabulary"].append(line)
                elif current_section == "grammar_tips":
                    sections["grammar_tips"].append(line)
    
    sections["response"] = sections["response"].strip()
    
    return sections
