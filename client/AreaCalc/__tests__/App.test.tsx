import React from 'react';
import { render } from '@testing-library/react-native';
import App from '../App'; // Adjust path if App.tsx is elsewhere

// Mock @react-native-community/netinfo
jest.mock('@react-native-community/netinfo', () => ({
  useNetInfo: jest.fn(() => ({ isConnected: true })),
  addEventListener: jest.fn(() => jest.fn()), // Returns an unsubscribe function
}));

// Mock react-native-image-picker
jest.mock('react-native-image-picker', () => ({
  launchImageLibrary: jest.fn(),
}));

// Mock react-native-picker-select
jest.mock('react-native-picker-select', () => {
  const React = require('react');
  const View = require('react-native').View;
  // A simple mock that renders its children, assuming it might wrap some content.
  // If it's a simple input, this might need to be adjusted or be even simpler.
  // For now, this allows the component to render without actual picker functionality.
  return (props) => <View>{props.children}</View>;
});


describe('<App />', () => {
  it('renders the main App component without crashing', () => {
    const { getByText } = render(<App />);
    // Check for a common element, e.g., the initial "Select Image" button
    // This text might change if the app's initial screen changes significantly
    expect(getByText('Select Image')).toBeTruthy();
  });

  // More tests could be added here to check for specific elements
  // or initial states if desired.
});
