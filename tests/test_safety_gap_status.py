from selene.safety_gap_status import safety_gap_status


def test_s1_s10_status_never_overstates_bounded_external_requirements():
    result = safety_gap_status()
    items = result["items"]

    assert items["S-01"]["state"] == "implemented"
    assert items["S-02"]["state"] == "implemented_for_installed_desktop"
    assert items["S-03"]["untrusted_or_broader_network_use_allowed"] is False
    assert items["S-05"]["lost_or_shared_device_protection_complete"] is False
    assert items["S-05"]["homegrown_cryptography_allowed"] is False
    assert items["S-06"]["code_signing_configured"] is False
    assert items["S-06"]["broad_public_distribution_ready"] is False
    assert items["S-08"]["encrypted_off_device_custody_complete"] is False
    assert items["S-10"]["state"] == "implemented_v1"
    assert result["identity_change"] is False
    assert result["governance_change"] is False
    assert result["autonomy_expansion"] is False
