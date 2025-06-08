import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Button,
  Image,
  Alert,
  StyleSheet,
  Platform,
  BackHandler,
} from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import { launchImageLibrary } from 'react-native-image-picker';
import RNPickerSelect from 'react-native-picker-select';
import axios from 'axios'; // Already imported, but good to ensure

const App = () => {
  const [isConnected, setIsConnected] = useState<boolean>(true);
  const [selectedImage, setSelectedImage] = useState<{ uri: string; type?: string; fileName?: string } | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);
  const [calculatedArea, setCalculatedArea] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [ocrOutput, setOcrOutput] = useState<string | null>(null);
  const [pixelArea, setPixelArea] = useState<number | null>(null);
  const [extractedNumbers, setExtractedNumbers] = useState<number[] | null>(null);
  const [calculationNotes, setCalculationNotes] = useState<string | null>(null);
  const [inputUnitDisplay, setInputUnitDisplay] = useState<string | null>(null);

  // Ensure axios is imported, though it might be there already
  // import axios from 'axios';

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsConnected(state.isConnected ?? false);
      if (!state.isConnected) {
        Alert.alert(
          'No Connection',
          'Please check your internet settings and try again.',
          [{ text: 'Close App', onPress: () => BackHandler.exitApp() }]
        );
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const handleSelectImage = () => {
    launchImageLibrary({ mediaType: 'photo' }, response => {
      if (response.didCancel) {
        console.log('User cancelled image picker');
      } else if (response.errorCode) {
        console.log('ImagePicker Error: ', response.errorMessage);
        setErrorMessage('Error selecting image: ' + response.errorMessage);
      } else if (response.assets && response.assets.length > 0) {
        const asset = response.assets[0];
        setSelectedImage({
          uri: asset.uri,
          type: asset.type,
          fileName: asset.fileName,
        });
        setCalculatedArea(null);
        setOcrOutput(null);
        setPixelArea(null);
        setExtractedNumbers(null);
        setCalculationNotes(null);
        setInputUnitDisplay(null);
        setErrorMessage(null); // Clear previous errors on new image selection
      }
    });
  };

  const handleCalculateArea = async () => {
    if (!selectedImage) {
      setErrorMessage("Please select an image first.");
      return;
    }
    if (!selectedUnit) {
      setErrorMessage("Please select a unit first.");
      return;
    }

    const formData = new FormData();
    formData.append('image', {
      uri: Platform.OS === 'android' ? selectedImage.uri : selectedImage.uri?.replace('file://', ''),
      type: selectedImage.type || 'image/jpeg', // Provide a default type if undefined
      name: selectedImage.fileName || 'image.jpg', // Provide a default name if undefined
    } as any); // Type assertion to satisfy FormData.append type checking for file
    formData.append('unit', selectedUnit);

    setCalculatedArea(null);
    setErrorMessage('Calculating...');

    try {
      // IMPORTANT: Replace <YOUR_LOCAL_IP> with the actual IP of your backend server.
      // For Android Emulator, often 10.0.2.2
      // For iOS Simulator or device on same network, your machine's local IP.
      const response = await axios.post('http://<YOUR_LOCAL_IP>:5000/calculate_area', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data) {
        setCalculatedArea(response.data.estimated_area_in_input_units || 'N/A');
        setInputUnitDisplay(response.data.input_unit || '');
        setOcrOutput(response.data.ocr_output || 'N/A');
        setPixelArea(response.data.largest_contour_area_pixels || null);
        setExtractedNumbers(response.data.extracted_numbers_from_ocr || []);
        setCalculationNotes(response.data.calculation_notes || 'No specific notes from server.');
        setErrorMessage(null); // Clear previous errors or "Calculating..."
      } else {
        setErrorMessage('Received an empty or unexpected response from server.');
        setCalculatedArea(null);
        setOcrOutput(null);
        setPixelArea(null);
        setExtractedNumbers(null);
        setCalculationNotes(null);
        setInputUnitDisplay(null);
      }
    } catch (error: any) {
      if (error.response) {
        setErrorMessage(error.response.data.error || 'Error from server.');
      } else if (error.request) {
        setErrorMessage('No response from server. Is it running? (Check IP address)');
      } else {
        setErrorMessage('Error setting up the request.');
      }
      console.error("Calculation error:", error);
      // Clear all result-specific states on error
      setCalculatedArea(null);
      setOcrOutput(null);
      setPixelArea(null);
      setExtractedNumbers(null);
      setCalculationNotes(null);
      setInputUnitDisplay(null);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.imagePreviewContainer}>
        {selectedImage ? (
          <Image source={{ uri: selectedImage.uri }} style={styles.imagePreview} />
        ) : (
          <Text>No image selected</Text>
        )}
      </View>
      <Button title="Select Image" onPress={handleSelectImage} />

      <RNPickerSelect
        onValueChange={(value) => {
          setSelectedUnit(value);
          setCalculatedArea(null);
          setOcrOutput(null);
          setPixelArea(null);
          setExtractedNumbers(null);
          setCalculationNotes(null);
          setInputUnitDisplay(null);
          setErrorMessage(null);
        }}
        items={[
          { label: 'cm', value: 'cm' },
          { label: 'inches', value: 'inches' },
          { label: 'meters', value: 'meters' },
          { label: 'custom', value: 'custom' },
        ]}
        placeholder={{ label: 'Select a unit...', value: null }}
        style={pickerSelectStyles}
      />

      <Button title="Calculate Area" onPress={handleCalculateArea} disabled={!selectedImage || !selectedUnit} />

      {/* Display Area for Results and Errors */}
      {errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

      {calculatedArea && (
        <View style={styles.resultsContainer}>
          <Text style={styles.resultText}>
            Estimated Area: {calculatedArea} {inputUnitDisplay && `(${inputUnitDisplay}²)`}
          </Text>

          {calculationNotes && (
            <Text style={styles.notesText}>{calculationNotes}</Text>
          )}

          <View style={styles.detailsContainer}>
            {ocrOutput && <Text><Text style={styles.resultLabel}>OCR Output:</Text> {ocrOutput}</Text>}
            {extractedNumbers && extractedNumbers.length > 0 && (
              <Text><Text style={styles.resultLabel}>Extracted Numbers:</Text> {extractedNumbers.join(', ')}</Text>
            )}
            {pixelArea !== null && (
              <Text><Text style={styles.resultLabel}>Detected Contour Area:</Text> {pixelArea} pixels²</Text>
            )}
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5', // Added a light background color
  },
  imagePreviewContainer: {
    width: 200,
    height: 200,
    borderWidth: 1,
    borderColor: '#ccc',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    backgroundColor: '#fff', // White background for preview area
  },
  imagePreview: {
    width: '100%',
    height: '100%',
    resizeMode: 'contain',
  },
  resultsContainer: {
    marginTop: 20,
    padding: 15, // Increased padding
    backgroundColor: '#ffffff', // White background for results
    borderRadius: 8, // Rounded corners
    borderWidth: 1,
    borderColor: '#e0e0e0', // Softer border color
    width: '100%', // Take full width
  },
  resultText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: 'green',
    marginBottom: 10, // Added margin
  },
  errorText: {
    marginTop: 10, // Consistent margin
    marginBottom: 10, // Added margin for spacing when results also show
    fontSize: 16,
    color: 'red',
    textAlign: 'center',
    width: '100%', // Take full width
  },
  notesText: {
    marginTop: 10,
    padding: 10, // Increased padding
    backgroundColor: '#f0f0f0',
    borderColor: '#dddddd', // Softer border
    borderWidth: 1,
    borderRadius: 4,
    fontSize: 13, // Slightly larger for readability
    color: '#333333', // Darker text for better contrast
    fontStyle: 'italic', // Italicize notes
  },
  detailsContainer: {
    marginTop: 15, // More space before details
    paddingTop: 10, // Space within details box
    borderTopWidth: 1,
    borderTopColor: '#eeeeee', // Light separator line
  },
  resultLabel: {
    fontWeight: 'bold',
    color: '#444444', // Slightly softer bold color
  },
});

const pickerSelectStyles = StyleSheet.create({
  inputIOS: {
    fontSize: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: 'gray',
    borderRadius: 4,
    color: 'black',
    paddingRight: 30, // to ensure the text is never behind the icon
    marginBottom: 20,
  },
  inputAndroid: {
    fontSize: 16,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderWidth: 0.5,
    borderColor: 'purple',
    borderRadius: 8,
    color: 'black',
    paddingRight: 30, // to ensure the text is never behind the icon
    marginBottom: 20,
  },
});

export default App;
