#!/usr/bin/env python3
"""
Analyze CDE Private School Data Files to identify new microschools in California (2021-2024)
Following the methodology from list-new-microschools guide
"""

import pandas as pd
import os
from pathlib import Path

def load_cde_files():
    """Load all four CDE private school data files"""
    files = {
        '2021-22': 'privateschooldata2122.xlsx',
        '2022-23': 'privateschooldata2223.xlsx', 
        '2023-24': 'privateschooldata2324.xlsx',
        '2024-25': 'privateschooldata2425.xlsx'
    }
    
    data = {}
    base_path = Path(__file__).parent
    
    for year, filename in files.items():
        filepath = base_path / filename
        if filepath.exists():
            try:
                df = pd.read_excel(filepath, engine='openpyxl')
                df['file_year'] = year
                data[year] = df
                print(f"Loaded {year}: {len(df)} schools")
                print(f"Columns: {list(df.columns)}")
                print(f"Sample data:\n{df.head(2)}\n")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        else:
            print(f"File not found: {filepath}")
    
    return data

def examine_data_structure(data):
    """Examine the structure of the data files"""
    print("=== DATA STRUCTURE ANALYSIS ===")
    
    for year, df in data.items():
        print(f"\n{year} Structure:")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Check for enrollment columns
        enrollment_cols = [col for col in df.columns if 'enroll' in col.lower() or 'total' in col.lower()]
        print(f"Enrollment-related columns: {enrollment_cols}")
        
        # Check for CDS code column
        cds_cols = [col for col in df.columns if 'cds' in col.lower() or 'code' in col.lower()]
        print(f"CDS-related columns: {cds_cols}")
        
        # Check for school name columns
        name_cols = [col for col in df.columns if 'name' in col.lower() or 'school' in col.lower()]
        print(f"Name-related columns: {name_cols}")

def find_first_appearances(data):
    """Apply first-appearance logic to identify when schools first appeared"""
    print("\n=== FIRST APPEARANCE ANALYSIS ===")
    
    if not data:
        print("No data available for analysis")
        return None
        
    # Combine all years of data
    all_data = []
    for year, df in data.items():
        df_copy = df.copy()
        df_copy['file_year'] = year
        all_data.append(df_copy)
    
    combined = pd.concat(all_data, ignore_index=True)
    print(f"Combined dataset: {len(combined)} total records")
    
    return combined

def main():
    """Main analysis function"""
    print("Starting CDE Private School Data Analysis")
    print("=" * 50)
    
    # Load the data files
    data = load_cde_files()
    
    if not data:
        print("No data files could be loaded. Please check file paths.")
        return
    
    # Examine data structure
    examine_data_structure(data)
    
    # Find first appearances
    combined_data = find_first_appearances(data)
    
    if combined_data is not None:
        print(f"\nSample combined data:")
        print(combined_data.head())

if __name__ == "__main__":
    main()