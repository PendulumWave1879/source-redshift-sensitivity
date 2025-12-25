from src.validate import validate_lens_inputs

def test_valid_inputs_pass_strict():
    res = validate_lens_inputs(theta_E_arcsec=1.2, z_l=0.3, z_s=1.1, strict=True)
    assert res['is_valid'] is True
    assert res['flags'] == []
    assert res['normalized']['theta_E_arcsec'] == 1.2
    assert res['normalized']['z_l'] == 0.3
    assert res['normalized']['z_s'] == 1.1

def test_zs_le_zl_fails_and_flags():
    res = validate_lens_inputs(theta_E_arcsec=1.2, z_l=0.8, z_s=0.8, strict=True)
    assert res['is_valid'] is False
    assert 'flag_zs_le_zl' in res['flags']
    assert res['normalized'] == {}

def test_thetaE_nonpositive_fails_and_flags():
    res = validate_lens_inputs(theta_E_arcsec=0.0, z_l=0.3, z_s=1.1, strict=True)
    assert res['is_valid'] is False
    assert 'flag_thetaE_nonpositive' in res['flags']

def test_missing_zs_fails_when_required():
    res = validate_lens_inputs(theta_E_arcsec=1.2, z_l=0.3, z_s=None, require_zs=True, strict=True)
    assert res['is_valid'] is False
    assert 'flag_missing_zs' in res['flags']

def test_missing_zs_allowed_when_not_required():
    res = validate_lens_inputs(theta_E_arcsec=1.2, z_l=0.3, z_s=None, require_zs=False, strict=True)
    assert res['is_valid'] is True
    assert res['flags'] == []
    assert 'z_s' not in res['normalized']
