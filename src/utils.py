def format_table_row(nhis, name, triage, status, ward, allergies):
    """Generates an even, highly scannable tabular alignment pattern for patient displays"""
    allergy_str = ", ".join(allergies) if allergies else "None"
    return f"|| {nhis:<8} | {name:<16} | {triage.upper():<8} | {status:<10} | {ward:<10} | {allergy_str:<20} ||"

# 
def print_patient_table(registry, width=50):
    if not registry:
        print("\n" + "="*width + "\n⚠️ No patients currently active.\n" + "="*width)
        return
    
    header = "|| {:<8} | {:<16} | {:<8} | {:<10} | {:<10} | {:<20} ||".format(
        "NHIS-ID", "PATIENT NAME", "TRIAGE", "STATUS", "WARD", "ALLERGIES"
    )
    sep = "=" * len(header)
    
    print("\n" + sep)
    print(f"|| {'PATIENT REGISTRY':^{len(header)-6}} ||")
    print(sep)
    print(header)
    print(sep)
    
    for nhis_id, p in registry.items():
        print(format_table_row(nhis_id, p['name'].upper(), p['triage'].upper(), p['status'].upper(), p['ward'].upper(),
            p.get('allergies', [])))
    
    print(sep)