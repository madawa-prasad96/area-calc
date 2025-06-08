import re

def extract_numbers_from_text(text: str) -> list[float]:
    numbers = []
    if text and text.strip():
        # Regex to find integers and decimals, including negative
        # Allows for numbers like 10, 10.5, .5, -.5, +5
        found_numbers = re.findall(r'[+-]?(?:\d+\.?\d*|\.\d+)', text)
        for num_str in found_numbers:
            try:
                # Avoid converting if it's just a sign or empty due to regex, though current regex is robust
                if num_str and num_str not in ['+', '-']:
                    numbers.append(float(num_str))
            except ValueError:
                pass  # Ignore if conversion fails
    return numbers

def estimate_area_from_pixels_and_ocr(
    pixel_area: float,
    ocr_numbers: list[float],
    unit: str = "units"
) -> tuple[float, str, str]:
    estimated_area_val = 0.0
    scale_info = "N/A"
    # Default notes
    notes = "Neither valid OCR numbers nor shape pixel area detected for estimation."


    if pixel_area <= 0:
        if not ocr_numbers:
            notes = "No shape detected (zero pixel area) and no OCR numbers found."
        else: # OCR numbers exist but no pixel area
            notes = "OCR numbers found, but no valid shape (zero pixel area) detected for scaling."
        return estimated_area_val, scale_info, notes

    # At this point, pixel_area > 0
    if not ocr_numbers:
        notes = "Shape detected (pixel area > 0), but no OCR numbers found to assist with scaling."
        return estimated_area_val, scale_info, notes

    positive_ocr_numbers = [n for n in ocr_numbers if n > 0]
    if not positive_ocr_numbers:
        notes = "Shape detected and OCR numbers found, but no positive OCR numbers available for scaling."
        return estimated_area_val, scale_info, notes

    potential_reference_length_from_ocr = max(positive_ocr_numbers)

    side_pixels = pixel_area**0.5 # Effective side length if shape were a square
    # side_pixels will be > 0 because pixel_area > 0

    scale_factor = potential_reference_length_from_ocr / side_pixels  # units/pixel
    estimated_area_val = pixel_area * (scale_factor**2)  # area in units^2

    scale_info = f"{potential_reference_length_from_ocr} {unit} / {side_pixels:.2f} pixels (estimated scale)"
    notes = (
        f"Highly approximate area. Assumed the largest positive detected number "
        f"({potential_reference_length_from_ocr} {unit}) "
        f"corresponds to one side of a square with the same area ({pixel_area:.2f} pixels²) as the detected shape outline. "
        f"This is a very rough estimation."
    )

    return estimated_area_val, scale_info, notes
