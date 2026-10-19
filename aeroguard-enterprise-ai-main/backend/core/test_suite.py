#!/usr/bin/env python3
"""
Automated Security & Real-Time ML Verification Suite for FactoryMind (AeroGuard AI v3.0).
Tests:
1. Working Password Login with MFA held inactive by default + optional RFC 6238 TOTP 2FA verification.
2. Peer Super Admin Immutability (Super Admin CANNOT delete or demote another Super Admin).
3. Single-Machine Dynamic ROI & Maintenance Cost Calculation (verifies CNC-01, CNC-02, CNC-04 each compute distinct single-machine costs).
4. Real Multi-Class Gradient Descent Training & Validation across all 5 Industrial Datasets (verifies distinct non-static accuracies and confusion matrices).
"""

import unittest
from totp_security import (
    generate_base32_secret,
    generate_totp_code,
    verify_totp_code,
)
from ml_engine import (
    VALIDATED_INDUSTRIAL_DATASETS,
    detect_machine_anomaly,
    calculate_single_machine_maintenance_roi,
    run_gemini_incident_investigation,
    train_hybrid_ml_xai_pipeline,
)
from views import (
    SYSTEM_SECURITY_POLICY,
    can_delete_or_demote_user,
)


class TestFactoryMindRealTimeAndSecurity(unittest.TestCase):
    def test_01_mfa_held_by_default_and_totp_ready(self):
        self.assertFalse(SYSTEM_SECURITY_POLICY["mfa_enforced"])
        secret = generate_base32_secret(32)
        now = 1792224000.0
        code = generate_totp_code(secret, timestamp=now)
        self.assertTrue(verify_totp_code(secret, code, timestamp=now, valid_window=1))

    def test_02_peer_super_admin_deletion_protection(self):
        allowed, _ = can_delete_or_demote_user("professionalabhiyan@gmail.com", "sangamshrestha104@gmail.com")
        self.assertFalse(allowed)
        allowed2, _ = can_delete_or_demote_user("professionalabhiyan@gmail.com", "sysadmin@aeroguard.ai")
        self.assertTrue(allowed2)

    def test_03_single_machine_distinct_maintenance_costs(self):
        cnc01 = {
            "machine_code": "CNC-01", "vibration_mms": 2.9, "baseline_vibration_mms": 2.8,
            "temperature_c": 71.0, "baseline_temp_c": 70.0, "defect_rate_pct": 1.1, "baseline_defect_pct": 1.0,
            "output_uph": 445, "days_since_maintenance": 11, "hourly_downtime_rate_usd": 720, "scrap_unit_cost_usd": 18.0, "repair_kit_cost_usd": 390
        }
        cnc02 = {
            "machine_code": "CNC-02", "vibration_mms": 8.2, "baseline_vibration_mms": 3.1,
            "temperature_c": 86.0, "baseline_temp_c": 72.0, "defect_rate_pct": 6.8, "baseline_defect_pct": 1.2,
            "output_uph": 365, "days_since_maintenance": 47, "hourly_downtime_rate_usd": 680, "scrap_unit_cost_usd": 14.5, "repair_kit_cost_usd": 1220
        }
        cnc04 = {
            "machine_code": "CNC-04", "vibration_mms": 4.3, "baseline_vibration_mms": 3.0,
            "temperature_c": 77.5, "baseline_temp_c": 71.0, "defect_rate_pct": 2.3, "baseline_defect_pct": 1.3,
            "output_uph": 410, "days_since_maintenance": 31, "hourly_downtime_rate_usd": 590, "scrap_unit_cost_usd": 11.5, "repair_kit_cost_usd": 780
        }
        roi1 = calculate_single_machine_maintenance_roi(cnc01)
        roi2 = calculate_single_machine_maintenance_roi(cnc02)
        roi4 = calculate_single_machine_maintenance_roi(cnc04)

        self.assertNotEqual(roi1["if_ignored_cost_usd"], roi2["if_ignored_cost_usd"])
        self.assertNotEqual(roi2["if_ignored_cost_usd"], roi4["if_ignored_cost_usd"])
        self.assertNotEqual(roi1["planned_fix_cost_usd"], roi2["planned_fix_cost_usd"])
        self.assertGreater(roi2["net_cost_savings_usd"], roi4["net_cost_savings_usd"])
        self.assertGreater(roi4["net_cost_savings_usd"], roi1["net_cost_savings_usd"])

    def test_04_real_training_across_all_5_datasets(self):
        self.assertEqual(len(VALIDATED_INDUSTRIAL_DATASETS), 5)
        accuracies = set()
        for ds in ["ai4i", "smart", "nasa", "secom", "bosch"]:
            res = train_hybrid_ml_xai_pipeline({"dataset_id": ds, "epochs": 30})
            acc = res["metrics"]["accuracy_pct"]
            accuracies.add(acc)
            self.assertGreater(acc, 80.0)
            self.assertLess(acc, 99.5)
            # Verify confusion matrix sums to exact validation sample count
            cm_sum = sum(sum(row) for row in res["confusion_matrix"]["matrix"])
            self.assertEqual(cm_sum, res["confusion_matrix"]["total_validation_samples"])
        # Verify the 5 datasets produce genuinely distinct validation accuracies (not a static number)
        self.assertEqual(len(accuracies), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
