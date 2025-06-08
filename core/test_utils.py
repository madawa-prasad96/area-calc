import pytest
from .utils import extract_numbers_from_text, estimate_area_from_pixels_and_ocr

def test_extract_numbers_from_text():
    assert extract_numbers_from_text("Size 10.5cm, other 20, -5.2") == [10.5, 20.0, -5.2]
    assert extract_numbers_from_text("No numbers here") == []
    assert extract_numbers_from_text("Value: 100") == [100.0]
    assert extract_numbers_from_text("0.5, .7, 1.") == [0.5, 0.7, 1.0]
    assert extract_numbers_from_text("-0.5, +.8") == [-0.5, 0.8]
    assert extract_numbers_from_text("Text with 123 and 45.67.") == [123.0, 45.67]
    assert extract_numbers_from_text("Only signs + -") == []
    assert extract_numbers_from_text("") == []
    assert extract_numbers_from_text("  ") == [] # Test with whitespace only
    assert extract_numbers_from_text("Number: -10") == [-10.0]


def test_estimate_area_from_pixels_and_ocr():
    # Case 1: Valid inputs
    area_val, scale, notes = estimate_area_from_pixels_and_ocr(100.0, [10.0, 5.0], "cm")
    # Expected: ref_ocr = 10. side_pixels = sqrt(100) = 10. scale_factor = 10/10 = 1.
    # estimated_area_val = 100 * (1^2) = 100.
    assert area_val == pytest.approx(100.0)
    assert "10.0 cm / 10.00 pixels" in scale
    assert "Highly approximate area" in notes
    assert "largest positive detected number (10.0 cm)" in notes # Check if the largest number is used

    # Case 2: No OCR numbers
    area_val, _, notes = estimate_area_from_pixels_and_ocr(100.0, [], "in")
    assert area_val == 0.0
    assert "no OCR numbers found" in notes # Adjusted to match new notes in utils

    # Case 3: Zero pixel area
    area_val, _, notes = estimate_area_from_pixels_and_ocr(0.0, [10.0], "m")
    assert area_val == 0.0
    assert "No shape detected (zero pixel area) and no OCR numbers found." not in notes # This case has OCR numbers
    assert "OCR numbers found, but no valid shape (zero pixel area) detected for scaling." in notes


    # Case 4: Only negative/zero OCR numbers
    area_val, _, notes = estimate_area_from_pixels_and_ocr(100.0, [-5.0, 0, -2.3], "cm")
    assert area_val == 0.0
    assert "no positive OCR numbers available for scaling" in notes # Adjusted

    # Case 5: Empty inputs (zero pixel area, no OCR numbers)
    area_val, _, notes = estimate_area_from_pixels_and_ocr(0, [], "") # Unit as empty string
    assert area_val == 0.0
    assert "No shape detected (zero pixel area) and no OCR numbers found." in notes

    # Case 6: Pixel area > 0, but no positive OCR numbers (only zero)
    area_val, _, notes = estimate_area_from_pixels_and_ocr(100.0, [0.0], "m")
    assert area_val == 0.0
    assert "no positive OCR numbers available for scaling" in notes

    # Case 7: Pixel area > 0, multiple positive OCR numbers, ensure max is used
    area_val, scale, notes = estimate_area_from_pixels_and_ocr(225.0, [10.0, 30.0, 5.0], "ft")
    # Expected: ref_ocr = 30. side_pixels = sqrt(225) = 15. scale_factor = 30/15 = 2.
    # estimated_area_val = 225 * (2^2) = 225 * 4 = 900
    assert area_val == pytest.approx(900.0)
    assert "30.0 ft / 15.00 pixels" in scale
    assert "largest positive detected number (30.0 ft)" in notes

    # Case 8: Very small pixel area (but > 0)
    area_val, scale, notes = estimate_area_from_pixels_and_ocr(0.0001, [1.0], "mm")
    # side_pixels = sqrt(0.0001) = 0.01
    # scale_factor = 1.0 / 0.01 = 100
    # area = 0.0001 * (100^2) = 0.0001 * 10000 = 1.0
    assert area_val == pytest.approx(1.0)
    assert "1.0 mm / 0.01 pixels" in scale
    assert "largest positive detected number (1.0 mm)" in notes
