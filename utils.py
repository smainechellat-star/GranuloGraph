"""
Utils Module - Utility functions for GranuloGraph
Includes file handling, data validation, and configuration management

Author: Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria

STANDARDS COMPLIANCE:
- ASTM D6913 (Recovered Weight method)
- NF P 94-056 / ISO 17892-4 (Initial Weight method)
- Folk & Ward (1957) - Complete 7-class sorting, 6-class kurtosis
- ISO 14688-1:2017 - Grain size classification
"""

import os
import csv
import json
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import re
import math


# ═══════════════════════════════════════════════════════════════════════════════
# Data Validator Class
# ═══════════════════════════════════════════════════════════════════════════════

class DataValidator:
    """Validate sieve analysis data"""
    
    @staticmethod
    def validate_diameter(diameter: float) -> Tuple[bool, str]:
        """
        Validate sieve diameter value
        
        Args:
            diameter: Sieve diameter in mm
            
        Returns:
            (is_valid, error_message)
        """
        if diameter <= 0:
            return False, "Diameter must be positive"
        if diameter > 1000:
            return False, "Diameter too large (>1000 mm)"
        if diameter < 0.0001:
            return False, "Diameter too small (<0.0001 mm)"
        return True, ""
    
    @staticmethod
    def validate_weight(weight: float) -> Tuple[bool, str]:
        """
        Validate retained weight value
        
        Args:
            weight: Retained weight in grams
            
        Returns:
            (is_valid, error_message)
        """
        if weight < 0:
            return False, "Weight cannot be negative"
        if weight > 10000:
            return False, "Weight too large (>10 kg)"
        return True, ""
    
    @staticmethod
    def validate_initial_weight(weight: float) -> Tuple[bool, str]:
        """
        Validate initial sample weight
        
        Args:
            weight: Initial sample weight in grams
            
        Returns:
            (is_valid, error_message)
        """
        if weight <= 0:
            return False, "Initial weight must be positive"
        if weight > 5000:
            return False, "Initial weight too large (>5 kg)"
        if weight < 0.1:
            return False, "Initial weight too small (<0.1 g)"
        return True, ""
    
    @staticmethod
    def validate_sieve_sequence(diameters: List[float]) -> Tuple[bool, str]:
        """
        Validate that sieves are in descending order (coarse to fine)
        
        Args:
            diameters: List of sieve diameters
            
        Returns:
            (is_valid, error_message)
        """
        if len(diameters) < 2:
            return True, ""  # Can't validate sequence with <2 sieves
            
        # Check if sorted in descending order
        if diameters != sorted(diameters, reverse=True):
            return False, "Sieves must be in descending order (coarse to fine)"
        
        # Check for duplicates
        if len(diameters) != len(set(diameters)):
            return False, "Duplicate sieve diameters found"
            
        return True, ""
    
    @staticmethod
    def validate_recovery(initial_weight: float, recovered_weight: float) -> Tuple[bool, str]:
        """
        Validate weight recovery percentage
        
        Args:
            initial_weight: Initial sample weight
            recovered_weight: Sum of all retained weights
            
        Returns:
            (is_valid, warning_message)
        """
        if initial_weight <= 0:
            return False, "Invalid initial weight"
            
        recovery_pct = (recovered_weight / initial_weight) * 100
        
        if 98 <= recovery_pct <= 102:
            return True, f"Recovery: {recovery_pct:.2f}% - Acceptable"
        elif 95 <= recovery_pct < 98:
            return True, f"Recovery: {recovery_pct:.2f}% - Low (possible fines loss)"
        elif 102 < recovery_pct <= 105:
            return True, f"Recovery: {recovery_pct:.2f}% - High (possible contamination)"
        else:
            return False, f"Recovery: {recovery_pct:.2f}% - Poor, re-run analysis"
    
    @staticmethod
    def validate_data_completeness(data: List[Tuple[float, float]], 
                                   min_rows: int = 10) -> Tuple[bool, str]:
        """
        Check if data has minimum required rows
        
        Args:
            data: List of (diameter, weight) tuples
            min_rows: Minimum number of rows required
            
        Returns:
            (is_valid, message)
        """
        if len(data) < min_rows:
            return False, f"Need at least {min_rows} sieve measurements (have {len(data)})"
        return True, f"Data complete: {len(data)} sieves"
    
    @staticmethod
    def validate_all(data: List[Tuple[float, float]], 
                     initial_weight: float) -> Dict[str, Any]:
        """
        Perform all validations
        
        Args:
            data: List of (diameter, weight) tuples
            initial_weight: Initial sample weight
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        if not data:
            results['is_valid'] = False
            results['errors'].append("No data provided")
            return results
            
        # Extract diameters and weights
        diameters = [d for d, _ in data]
        weights = [w for _, w in data]
        recovered_weight = sum(weights)
        
        # Validate initial weight
        valid, msg = DataValidator.validate_initial_weight(initial_weight)
        if not valid:
            results['is_valid'] = False
            results['errors'].append(msg)
        
        # Validate each diameter
        for i, d in enumerate(diameters):
            valid, msg = DataValidator.validate_diameter(d)
            if not valid:
                results['is_valid'] = False
                results['errors'].append(f"Row {i+1}: {msg}")
        
        # Validate each weight
        for i, w in enumerate(weights):
            valid, msg = DataValidator.validate_weight(w)
            if not valid:
                results['is_valid'] = False
                results['errors'].append(f"Row {i+1}: {msg}")
        
        # Validate sieve sequence
        valid, msg = DataValidator.validate_sieve_sequence(diameters)
        if not valid:
            results['is_valid'] = False
            results['errors'].append(msg)
        
        # Validate recovery (warning only)
        valid, msg = DataValidator.validate_recovery(initial_weight, recovered_weight)
        if not valid:
            results['warnings'].append(msg)
        elif 'Low' in msg or 'High' in msg:
            results['warnings'].append(msg)
        
        # Validate data completeness
        valid, msg = DataValidator.validate_data_completeness(data)
        if not valid:
            results['is_valid'] = False
            results['errors'].append(msg)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# File Handler Class
# ═══════════════════════════════════════════════════════════════════════════════

class FileHandler:
    """Handle file operations for sieve analysis data"""
    
    @staticmethod
    def parse_number(value: str) -> Optional[float]:
        """
        Parse number from string, handling both comma and point decimals
        
        Args:
            value: String representation of number
            
        Returns:
            Float value or None if invalid
        """
        if not value or not value.strip():
            return None
            
        # Remove whitespace and replace comma with point
        cleaned = value.strip().replace(',', '.')
        
        # Remove any non-numeric characters except . and -
        cleaned = re.sub(r'[^\d.-]', '', cleaned)
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    @staticmethod
    def load_csv(filename: str) -> Tuple[List[Tuple[float, float]], Optional[float], str]:
        """
        Load data from CSV file
        
        Expected formats:
        - Two columns: diameter, weight
        - Optional third column: initial_weight (same for all rows)
        - Optional fourth column: calculation_basis (RECOVERED or INITIAL)
        - Or first row: metadata like "Initial weight: 100.0"
        
        Args:
            filename: Path to CSV file
            
        Returns:
            (data, initial_weight, calculation_basis) tuple
        """
        data = []
        initial_weight = None
        calculation_basis = "RECOVERED"  # Default to ASTM
        
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    # Check for metadata in comments
                    if 'initial' in line.lower() and 'weight' in line.lower():
                        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line.replace(',', '.'))
                        if numbers:
                            initial_weight = float(numbers[0])
                    elif 'basis' in line.lower() or 'method' in line.lower():
                        if 'initial' in line.lower():
                            calculation_basis = "INITIAL"
                        elif 'recovered' in line.lower():
                            calculation_basis = "RECOVERED"
                    continue
                    
                # Split by comma, semicolon, or whitespace
                parts = re.split(r'[,\s;]+', line)
                if len(parts) >= 2:
                    d_val = FileHandler.parse_number(parts[0])
                    w_val = FileHandler.parse_number(parts[1])
                    
                    if d_val is not None and w_val is not None:
                        data.append((d_val, w_val))
                        
                        # Check for initial weight in third column
                        if len(parts) >= 3 and initial_weight is None:
                            iw_val = FileHandler.parse_number(parts[2])
                            if iw_val is not None:
                                initial_weight = iw_val
                        
                        # Check for calculation basis in fourth column
                        if len(parts) >= 4:
                            basis_str = parts[3].strip().upper()
                            if basis_str in ['RECOVERED', 'INITIAL']:
                                calculation_basis = basis_str
            
            # Sort by diameter descending
            data.sort(key=lambda x: x[0], reverse=True)
            
            return data, initial_weight, calculation_basis
            
        except Exception as e:
            raise Exception(f"Error loading CSV: {str(e)}")
    
    @staticmethod
    def load_excel(filename: str) -> Tuple[List[Tuple[float, float]], Optional[float], str]:
        """
        Load data from Excel file
        
        Args:
            filename: Path to Excel file
            
        Returns:
            (data, initial_weight, calculation_basis) tuple
        """
        try:
            df = pd.read_excel(filename, header=None)
            data = []
            initial_weight = None
            calculation_basis = "RECOVERED"  # Default to ASTM
            
            for idx, row in df.iterrows():
                if len(row) >= 2:
                    d_val = FileHandler.parse_number(str(row[0]))
                    w_val = FileHandler.parse_number(str(row[1]))
                    
                    if d_val is not None and w_val is not None:
                        data.append((d_val, w_val))
                    
                    # Check for initial weight in third column
                    if len(row) >= 3 and initial_weight is None:
                        iw_val = FileHandler.parse_number(str(row[2]))
                        if iw_val is not None:
                            initial_weight = iw_val
                    
                    # Check for calculation basis in fourth column
                    if len(row) >= 4:
                        basis_str = str(row[3]).strip().upper()
                        if basis_str in ['RECOVERED', 'INITIAL']:
                            calculation_basis = basis_str
            
            # Sort by diameter descending
            data.sort(key=lambda x: x[0], reverse=True)
            
            return data, initial_weight, calculation_basis
            
        except Exception as e:
            raise Exception(f"Error loading Excel file: {str(e)}")
    
    @staticmethod
    def load_data(filename: str) -> Tuple[List[Tuple[float, float]], Optional[float], str]:
        """
        Load data from file (auto-detect format)
        
        Args:
            filename: Path to file
            
        Returns:
            (data, initial_weight, calculation_basis) tuple
        """
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.csv':
            return FileHandler.load_csv(filename)
        elif ext in ['.xlsx', '.xls']:
            return FileHandler.load_excel(filename)
        elif ext == '.txt':
            # Try as CSV first
            return FileHandler.load_csv(filename)
        else:
            raise Exception(f"Unsupported file format: {ext}")
    
    @staticmethod
    def save_csv(filename: str, data: List[Tuple[float, float]], 
                 initial_weight: float, calculation_basis: str = "RECOVERED",
                 include_metadata: bool = True):
        """
        Save data to CSV file
        
        Args:
            filename: Output filename
            data: List of (diameter, weight) tuples
            initial_weight: Initial sample weight
            calculation_basis: "RECOVERED" or "INITIAL"
            include_metadata: Whether to include metadata header
        """
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if include_metadata:
                    writer.writerow(['# GranuloGraph Export'])
                    writer.writerow(['# Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                    writer.writerow(['# Initial weight (g):', f'{initial_weight:.4f}'])
                    writer.writerow(['# Calculation Basis:', calculation_basis])
                    writer.writerow([])
                
                writer.writerow(['Diameter_mm', 'Weight_g', 'Initial_Weight_g', 'Calculation_Basis'])
                
                for d, w in data:
                    writer.writerow([f'{d:.6f}'.rstrip('0').rstrip('.'), 
                                    f'{w:.4f}'.rstrip('0').rstrip('.'),
                                    f'{initial_weight:.4f}',
                                    calculation_basis])
                        
        except Exception as e:
            raise Exception(f"Error saving CSV: {str(e)}")
    
    @staticmethod
    def save_excel(filename: str, data: List[Tuple[float, float]], 
                   initial_weight: float, calculation_basis: str = "RECOVERED",
                   results: Optional[Dict] = None):
        """
        Save data to Excel file with multiple sheets
        
        Args:
            filename: Output filename
            data: List of (diameter, weight) tuples
            initial_weight: Initial sample weight
            calculation_basis: "RECOVERED" or "INITIAL"
            results: Optional dictionary of calculated parameters
        """
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Raw data sheet
                df_raw = pd.DataFrame(data, columns=['Diameter_mm', 'Weight_g'])
                df_raw['Initial_Weight_g'] = initial_weight
                df_raw['Calculation_Basis'] = calculation_basis
                df_raw.to_excel(writer, sheet_name='Raw Data', index=False)
                
                # If results provided, create parameters sheet
                if results:
                    params = []
                    values = []
                    
                    for key, value in results.items():
                        if not isinstance(value, (dict, list)):
                            params.append(key)
                            values.append(value)
                    
                    df_params = pd.DataFrame({
                        'Parameter': params,
                        'Value': values
                    })
                    df_params.to_excel(writer, sheet_name='Parameters', index=False)
                
                # Auto-adjust column widths
                for sheet in writer.sheets:
                    worksheet = writer.sheets[sheet]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                        
        except Exception as e:
            raise Exception(f"Error saving Excel file: {str(e)}")
    
    @staticmethod
    def export_results(filename: str, results: Dict, calculation_basis: str = "RECOVERED"):
        """
        Export calculation results to file
        
        Args:
            filename: Output filename
            results: Dictionary of results
            calculation_basis: "RECOVERED" or "INITIAL"
        """
        ext = os.path.splitext(filename)[1].lower()
        
        # Add calculation basis to results
        results['calculation_basis'] = calculation_basis
        results['export_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Flatten nested dictionaries
        flat_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    flat_results[f"{key}_{subkey}"] = subvalue
            else:
                flat_results[key] = value
        
        if ext == '.csv':
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Parameter', 'Value'])
                for key, value in flat_results.items():
                    writer.writerow([key, value])
        
        elif ext in ['.xlsx', '.xls']:
            df = pd.DataFrame(list(flat_results.items()), 
                            columns=['Parameter', 'Value'])
            df.to_excel(filename, index=False)
        
        else:
            # Default to CSV
            filename = filename + '.csv'
            FileHandler.export_results(filename, results, calculation_basis)


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration Manager Class
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_file: str = 'granulograph_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def default_config(self) -> Dict:
        """Return default configuration"""
        return {
            'appearance': {
                'theme': 'default',
                'font_size': 10,
                'show_grid': True,
                'graph_dpi': 100
            },
            'analysis': {
                'default_initial_weight': 100.0,
                'min_sieves': 10,
                'recovery_tolerance': 98.0,
                'use_phi_scale': True,
                'default_calculation_basis': 'RECOVERED'  # ✅ ADD: Default to ASTM
            },
            'export': {
                'graph_format': 'png',
                'graph_dpi': 300,
                'include_metadata': True,
                'decimal_places': 4
            },
            'recent_files': [],
            'last_directory': os.path.expanduser('~')
        }
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default = self.default_config()
                    return self.merge_configs(default, config)
            return self.default_config()
        except Exception:
            return self.default_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Recursively merge configurations"""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def add_recent_file(self, filename: str):
        """Add file to recent files list"""
        recent = self.config.get('recent_files', [])
        
        # Remove if already exists
        if filename in recent:
            recent.remove(filename)
        
        # Add to front
        recent.insert(0, filename)
        
        # Keep only last 10
        self.config['recent_files'] = recent[:10]
        self.save_config()
    
    def get_calculation_basis(self) -> str:
        """Get default calculation basis preference"""
        return self.config.get('analysis', {}).get('default_calculation_basis', 'RECOVERED')
    
    def set_calculation_basis(self, basis: str):
        """Set default calculation basis preference"""
        if basis in ['RECOVERED', 'INITIAL']:
            self.set('analysis.default_calculation_basis', basis)


# ═══════════════════════════════════════════════════════════════════════════════
# Unit Converter Class
# ═══════════════════════════════════════════════════════════════════════════════

class UnitConverter:
    """Handle unit conversions"""
    
    @staticmethod
    def mm_to_phi(diameter_mm: float) -> float:
        """
        Convert diameter in mm to phi (φ) units
        φ = -log₂(diameter in mm)
        """
        if diameter_mm <= 0:
            return float('inf')
        return -math.log2(diameter_mm)
    
    @staticmethod
    def phi_to_mm(phi: float) -> float:
        """
        Convert phi (φ) to diameter in mm
        d = 2^(-φ)
        """
        return 2 ** (-phi)
    
    @staticmethod
    def mm_to_um(diameter_mm: float) -> float:
        """Convert mm to micrometers"""
        return diameter_mm * 1000
    
    @staticmethod
    def um_to_mm(diameter_um: float) -> float:
        """Convert micrometers to mm"""
        return diameter_um / 1000
    
    @staticmethod
    def mm_to_inch(diameter_mm: float) -> float:
        """Convert mm to inches"""
        return diameter_mm / 25.4
    
    @staticmethod
    def inch_to_mm(diameter_inch: float) -> float:
        """Convert inches to mm"""
        return diameter_inch * 25.4
    
    @staticmethod
    def g_to_kg(weight_g: float) -> float:
        """Convert grams to kilograms"""
        return weight_g / 1000
    
    @staticmethod
    def kg_to_g(weight_kg: float) -> float:
        """Convert kilograms to grams"""
        return weight_kg * 1000
    
    @staticmethod
    def get_wentworth_class(diameter_mm: float) -> str:
        """
        Get Wentworth (1922) classification for a grain size
        
        Args:
            diameter_mm: Grain diameter in mm
            
        Returns:
            Classification name
        """
        if diameter_mm >= 256:
            return "Boulder"
        elif diameter_mm >= 64:
            return "Cobble"
        elif diameter_mm >= 4:
            return "Pebble"
        elif diameter_mm >= 2:
            return "Granule"
        elif diameter_mm >= 1:
            return "Very coarse sand"
        elif diameter_mm >= 0.5:
            return "Coarse sand"
        elif diameter_mm >= 0.25:
            return "Medium sand"
        elif diameter_mm >= 0.125:
            return "Fine sand"
        elif diameter_mm >= 0.0625:
            return "Very fine sand"
        elif diameter_mm >= 0.0039:
            return "Silt"
        else:
            return "Clay"
    
    @staticmethod
    def get_iso_14688_class(diameter_mm: float) -> str:
        """
        Get ISO 14688-1:2017 classification for a grain size
        
        Args:
            diameter_mm: Grain diameter in mm
            
        Returns:
            Classification name
        """
        if diameter_mm >= 630:
            return "Boulder"
        elif diameter_mm >= 200:
            return "Cobble"
        elif diameter_mm >= 63:
            return "Gravel (Coarse)"
        elif diameter_mm >= 20:
            return "Gravel (Medium)"
        elif diameter_mm >= 6.3:
            return "Gravel (Fine)"
        elif diameter_mm >= 2.0:
            return "Sand (Coarse)"
        elif diameter_mm >= 0.63:
            return "Sand (Medium)"
        elif diameter_mm >= 0.2:
            return "Sand (Fine)"
        elif diameter_mm >= 0.063:
            return "Silt (Coarse)"
        elif diameter_mm >= 0.02:
            return "Silt (Medium)"
        elif diameter_mm >= 0.0063:
            return "Silt (Fine)"
        elif diameter_mm >= 0.002:
            return "Silt (Clayey)"
        else:
            return "Clay"


# ═══════════════════════════════════════════════════════════════════════════════
# Statistics Helper Class
# ═══════════════════════════════════════════════════════════════════════════════

class StatisticsHelper:
    """Helper functions for statistical calculations"""
    
    @staticmethod
    def percentile_interpolate(percentiles: List[float], values: List[float], 
                                target: float) -> float:
        """
        Interpolate to find value at target percentile
        
        Args:
            percentiles: List of percentile values (0-100)
            values: Corresponding values
            target: Target percentile
            
        Returns:
            Interpolated value
        """
        from scipy import interpolate
        
        # Remove NaN values
        valid_idx = [i for i, v in enumerate(values) if not np.isnan(v)]
        if len(valid_idx) < 2:
            return float('nan')
            
        p_valid = [percentiles[i] for i in valid_idx]
        v_valid = [values[i] for i in valid_idx]
        
        # Sort by percentile
        pairs = sorted(zip(p_valid, v_valid))
        p_sorted = [p[0] for p in pairs]
        v_sorted = [p[1] for p in pairs]
        
        try:
            f = interpolate.interp1d(p_sorted, v_sorted, bounds_error=False,
                                     fill_value=(v_sorted[0], v_sorted[-1]))
            return float(f(target))
        except:
            return float('nan')
    
    @staticmethod
    def calculate_mode_frequency(values: List[float], frequencies: List[float]) -> float:
        """
        Calculate mode from frequency distribution
        
        Args:
            values: Class midpoints or sieve sizes
            frequencies: Frequencies for each class
            
        Returns:
            Mode value
        """
        if not values or not frequencies:
            return float('nan')
            
        max_freq_idx = frequencies.index(max(frequencies))
        
        if max_freq_idx == 0:
            return values[0]
        elif max_freq_idx == len(values) - 1:
            return values[-1]
        else:
            # Simple interpolation
            return values[max_freq_idx]
    
    @staticmethod
    def classify_sorting(sorting_value: float) -> str:
        """
        Classify sorting value (Folk & Ward, 1957)
        ✅ FIX: Complete 7-class scale (was missing 2 classes)
        """
        if sorting_value < 0.35:
            return "Very well sorted"
        elif sorting_value < 0.50:
            return "Well sorted"
        elif sorting_value < 0.71:
            return "Moderately well sorted"
        elif sorting_value < 1.00:
            return "Moderately sorted"          # ✅ ADDED
        elif sorting_value < 2.00:
            return "Poorly sorted"
        elif sorting_value < 4.00:
            return "Very poorly sorted"
        else:
            return "Extremely poorly sorted"    # ✅ ADDED
    
    @staticmethod
    def classify_skewness(skewness_value: float) -> str:
        """Classify skewness value (Folk & Ward)"""
        if skewness_value < -0.3:
            return "Strongly coarse skewed"
        elif skewness_value < -0.1:
            return "Coarse skewed"
        elif skewness_value < 0.1:
            return "Near symmetrical"
        elif skewness_value < 0.3:
            return "Fine skewed"
        else:
            return "Strongly fine skewed"
    
    @staticmethod
    def classify_kurtosis(kurtosis_value: float) -> str:
        """
        Classify kurtosis value (Folk & Ward, 1957)
        ✅ FIX: Complete 6-class scale (was missing 1 class)
        """
        if kurtosis_value < 0.67:
            return "Very platykurtic"
        elif kurtosis_value < 0.90:
            return "Platykurtic"
        elif kurtosis_value < 1.11:
            return "Mesokurtic"
        elif kurtosis_value < 1.50:
            return "Leptokurtic"
        elif kurtosis_value < 3.00:
            return "Very leptokurtic"
        else:
            return "Extremely leptokurtic"      # ✅ ADDED
    
    @staticmethod
    def classify_fm(fm_value: float) -> Tuple[str, str]:
        """
        Classify Fineness Modulus with engineering notes
        
        Returns:
            (classification, engineering_note)
        """
        if fm_value < 2.2:
            return ("Very fine sand", 
                    "RISK OF SHRINKAGE AND CRACKING - Not suitable for structural concrete")
        elif fm_value < 2.6:
            return ("Fine sand", 
                    "Ideal for finishing coats, may need more cement for concrete")
        elif fm_value < 2.9:
            return ("Medium sand", 
                    "PREFERRED for high-quality concrete - Optimal workability and strength")
        elif fm_value < 3.2:
            return ("Coarse sand", 
                    "For high-strength concrete, may be harsh if poorly graded")
        else:
            return ("Very coarse sand", 
                    "STONY/HARSH concrete - Difficult to finish, poor workability")
    
    @staticmethod
    def classify_cu(cu_value: float) -> str:
        """
        Classify Uniformity Coefficient (ASTM D2487)
        
        Returns:
            Classification string
        """
        if cu_value >= 6:
            return "Well-graded (Cu ≥ 6)"
        elif cu_value >= 2:
            return "Moderately graded (2 ≤ Cu < 6)"
        else:
            return "Poorly graded / uniform (Cu < 2)"
    
    @staticmethod
    def classify_cc(cc_value: float) -> str:
        """
        Classify Curvature Coefficient (ASTM D2487)
        
        Returns:
            Classification string
        """
        if 1.0 <= cc_value <= 3.0:
            return "Well-graded (1 ≤ Cc ≤ 3)"
        else:
            return "Poorly graded (Cc outside 1-3)"


# ═══════════════════════════════════════════════════════════════════════════════
# Report Generator Class (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """Generate formatted reports for export"""
    
    @staticmethod
    def generate_text_report(results: Dict, calculation_basis: str = "RECOVERED") -> str:
        """
        Generate a formatted text report
        
        Args:
            results: Dictionary of calculation results
            calculation_basis: "RECOVERED" or "INITIAL"
            
        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 60)
        report.append("GRANULOGRAPH - GRAIN-SIZE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Calculation Basis: {calculation_basis}")
        report.append("=" * 60)
        
        # Percentiles
        report.append("\nPERCENTILES:")
        report.append("-" * 60)
        for p in [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]:
            d_key = f'D{p}'
            phi_key = f'phi{p}'
            if d_key in results and phi_key in results:
                report.append(f"  D{p:2d} = {results[d_key]:8.4f} mm  (φ = {results[phi_key]:6.3f})")
        
        # Folk & Ward Statistics
        report.append("\nFOLK & WARD (1957) STATISTICS:")
        report.append("-" * 60)
        if 'mean_phi' in results:
            report.append(f"  Graphic Mean:  {results['mean_phi']:.3f} φ  ({results['mean_mm']:.4f} mm)")
        if 'median_phi' in results:
            report.append(f"  Median:        {results['median_phi']:.3f} φ  ({results['median_mm']:.4f} mm)")
        if 'sorting' in results:
            report.append(f"  Sorting (σI):  {results['sorting']:.3f}  →  {results['sorting_class']}")
        if 'skewness' in results:
            report.append(f"  Skewness (Sk): {results['skewness']:.3f}  →  {results['skewness_class']}")
        if 'kurtosis' in results:
            report.append(f"  Kurtosis (KG): {results['kurtosis']:.3f}  →  {results['kurtosis_class']}")
        
        # Geotechnical Parameters
        report.append("\nGEOTECHNICAL PARAMETERS:")
        report.append("-" * 60)
        if 'Cu' in results:
            report.append(f"  Uniformity Coeff. (Cu):  {results['Cu']:.2f}  →  {results['Cu_class']}")
        if 'Cc' in results:
            report.append(f"  Curvature Coeff. (Cc):   {results['Cc']:.2f}  →  {results['Cc_class']}")
        if 'FM' in results:
            report.append(f"  Fineness Modulus (FM):   {results['FM']:.2f}  →  {results['FM_class']}")
        
        # Quality Control
        report.append("\nQUALITY CONTROL:")
        report.append("-" * 60)
        if 'initial_weight' in results:
            report.append(f"  Initial Weight:   {results['initial_weight']:.3f} g")
        if 'recovered_weight' in results:
            report.append(f"  Recovered Weight: {results['recovered_weight']:.3f} g")
        if 'recovery_pct' in results:
            report.append(f"  Recovery:         {results['recovery_pct']:.2f}%")
        
        report.append("\n" + "=" * 60)
        report.append("End of Report")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    @staticmethod
    def save_text_report(filename: str, results: Dict, calculation_basis: str = "RECOVERED"):
        """
        Save text report to file
        
        Args:
            filename: Output filename
            results: Dictionary of calculation results
            calculation_basis: "RECOVERED" or "INITIAL"
        """
        try:
            report = ReportGenerator.generate_text_report(results, calculation_basis)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
        except Exception as e:
            raise Exception(f"Error saving text report: {str(e)}")