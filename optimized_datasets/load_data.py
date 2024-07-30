"""
This file contains the function that loads the features and labels from the updated dataset
"""


import os
import h5py
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import LabelEncoder, StandardScaler
from keras.layers import Dense, Dropout, Flatten, Conv1D, MaxPooling1D
from keras.utils import to_categorical
from keras.models import Sequential
from keras.callbacks import EarlyStopping
import joblib
from feature_extraction import extract_features


def load_data(h5_folder):
    """
    Load and process data from H5 files in the specified folder using extract_features.
    Includes data augmentation and feature selection.

    :param h5_folder: Path to the folder containing H5 files
    :return: Tuple of scaled features and one-hot encoded labels
    """
    features = []
    labels = []
    feature_length = None

    for filename in os.listdir(h5_folder):
        if filename.endswith('.h5'):
            file_path = os.path.join(h5_folder, filename)
            with h5py.File(file_path, 'r') as f:
                try:
                    # Extract features
                    feature = extract_features(f)

                    # If feature is a dictionary, flatten it
                    if isinstance(feature, dict):
                        feature = flatten_dict(feature)

                    # Ensure feature is a list or numpy array
                    feature = np.array(feature, dtype=float)

                    # Determine feature length from the first successful extraction
                    if feature_length is None:
                        feature_length = len(feature)

                    # Ensure feature vector has consistent length
                    if len(feature) < feature_length:
                        feature = np.pad(
                            feature, (0, feature_length - len(feature)))
                    elif len(feature) > feature_length:
                        feature = feature[:feature_length]

                    features.append(feature)
                    labels.append(f.attrs['genre'])

                    # Simple data augmentation: add slightly modified version of the same sample
                    augmented_feature = feature + \
                        np.random.normal(0, 0.05, feature.shape)
                    features.append(augmented_feature)
                    labels.append(f.attrs['genre'])

                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")

    features = np.array(features)
    labels = np.array(labels)

    # Encode labels
    label_encoder = LabelEncoder()
    labels_encoded = label_encoder.fit_transform(labels)

    # Apply SMOTE to balance the dataset
    smote = SMOTE(random_state=42)
    features_resampled, labels_resampled = smote.fit_resample(
        features, labels_encoded)

    # Feature scaling
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_resampled)

    # Feature selection
    selector = SelectKBest(f_classif, k=min(100, features_scaled.shape[1]))
    features_selected = selector.fit_transform(
        features_scaled, labels_resampled)

    # Convert labels to one-hot encoding
    labels_onehot = to_categorical(labels_resampled)

    # save the labels for future use
    joblib.dump(label_encoder, 'label_encoder.pkl')

    return features_selected, labels_onehot