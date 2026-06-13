from database.connection import DBContext

def add_asc():
    try:
        with DBContext() as (conn, cursor):
            # Check if ASC exists
            cursor.execute("SELECT reagent_id FROM reagents WHERE reagent_name = 'ASC'")
            if cursor.fetchone():
                print("ASC already exists.")
                return

            print("Adding ASC to reagents...")
            cursor.execute("INSERT INTO reagents (reagent_name, reagent_label, brand, param_type, display_order) VALUES ('ASC', '維生素C', 'LabStrip', 2, 13)")
            reagent_id = cursor.lastrowid
            
            print(f"Added ASC with reagent_id={reagent_id}")
            
            # Add QC Levels (Level 1, Level 2)
            cursor.execute("INSERT INTO qc_levels (reagent_id, level_name, vendor_id, qc_material) VALUES (%s, 'Level 1', 1, 'Quantimetrix')", (reagent_id,))
            lv1_id = cursor.lastrowid
            cursor.execute("INSERT INTO qc_levels (reagent_id, level_name, vendor_id, qc_material) VALUES (%s, 'Level 2', 1, 'Quantimetrix')", (reagent_id,))
            lv2_id = cursor.lastrowid
            
            print(f"Added QC Levels: L1={lv1_id}, L2={lv2_id}")
            
            # Add IQI for instrument 1 (77-1) and 2 (77-2)
            for inst_id in [1, 2]:
                cursor.execute("INSERT INTO instrument_qc_items (instrument_id, reagent_id, level_id, display_order) VALUES (%s, %s, %s, %s)", (inst_id, reagent_id, lv1_id, 25 if inst_id==1 else 49))
                cursor.execute("INSERT INTO instrument_qc_items (instrument_id, reagent_id, level_id, display_order) VALUES (%s, %s, %s, %s)", (inst_id, reagent_id, lv2_id, 26 if inst_id==1 else 50))
            
            print("Successfully added ASC and related configuration!")
    except Exception as e:
        print(f"Failed to add ASC: {e}")

if __name__ == "__main__":
    add_asc()
