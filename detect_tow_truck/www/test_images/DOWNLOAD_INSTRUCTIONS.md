# Download Test Images

## Required Images
Download these images and save them in `/config/www/test_images/` in your Home Assistant installation:

### 1. tow_truck.jpg
Search for: "tow truck street scene"
- **Recommended source**: https://www.pexels.com/search/tow%20truck/
- **Alternative**: https://pixabay.com/images/search/tow%20truck/
- Look for: Clear photo of a tow truck on a street or highway
- Save as: `tow_truck.jpg`

### 2. patrol_car.jpg  
Search for: "police car patrol car street"
- **Recommended source**: https://www.pexels.com/search/police%20car/
- **Alternative**: https://pixabay.com/images/search/police%20car/
- Look for: Clear photo of a police/patrol car on a street
- Save as: `patrol_car.jpg`

### 3. normal_street.jpg
Search for: "empty street scene no vehicles"
- **Recommended source**: https://www.pexels.com/search/empty%20street/
- **Alternative**: https://pixabay.com/images/search/street%20scene/
- Look for: Street scene with no prominent vehicles (for negative testing)
- Save as: `normal_street.jpg`

## Free Image Sources
- **Pexels** (https://www.pexels.com) - Free for commercial use
- **Pixabay** (https://pixabay.com) - Free images
- **Unsplash** (https://unsplash.com) - Free high-resolution photos

## Testing
Once downloaded:
1. Enable test mode: `input_boolean.test_tow_truck_mode = ON`
2. Select test image: `input_select.test_image_select`
3. Trigger motion sensor to test AI detection