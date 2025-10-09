from flask import Flask, request, jsonify, render_template_string
import cv2
import numpy as np
from flask_cors import CORS
import base64
import os
from datetime import datetime
import json
import hashlib
import secrets
from functools import wraps
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app, resources={r"/analyze": {"origins": "*"}}) 

logging.basicConfig(filename='app.log', level=logging.ERROR)

LICENSE_KEY = hashlib.sha256(b"KHAN_MOHD_ASIM_2025").hexdigest()

def check_license(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        license_key = request.headers.get('X-License-Key', '')
        if hashlib.sha256(license_key.encode()).hexdigest() != LICENSE_KEY:
            return jsonify({'error': 'Invalid or missing license key'}), 403
        return f(*args, **kwargs)
    return decorated_function

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Analytics AI - By Khan Mohd Asim</title>
    <meta name="author" content="Khan Mohd Asim">
    <meta name="copyright" content="Copyright 2025 Khan Mohd Asim">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            user-select: none;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e8e8e8;
            min-height: 100vh;
            padding: 20px;
        }

        .watermark {
            position: fixed;
            bottom: 20px;
            right: 20px;
            color: rgba(206, 147, 108, 0.3);
            font-size: 0.8rem;
            font-weight: 600;
            z-index: 1000;
            pointer-events: none;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 12px;
            letter-spacing: -0.02em;
        }

        .header .subtitle {
            font-size: 1.1rem;
            color: #a0a0b0;
            font-weight: 400;
        }

        .developer-badge {
            display: inline-block;
            background: rgba(206, 147, 108, 0.1);
            border: 1px solid rgba(206, 147, 108, 0.3);
            padding: 8px 16px;
            border-radius: 20px;
            color: #ce936c;
            font-size: 0.9rem;
            margin-top: 12px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        }

        .tab {
            padding: 12px 24px;
            background: transparent;
            border: none;
            color: #a0a0b0;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            border-radius: 8px 8px 0 0;
            transition: all 0.3s ease;
        }

        .tab:hover {
            color: #ce936c;
            background: rgba(206, 147, 108, 0.05);
        }

        .tab.active {
            color: #ce936c;
            background: rgba(206, 147, 108, 0.1);
            border-bottom: 2px solid #ce936c;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }

        .upload-section {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }

        .upload-section:hover {
            border-color: rgba(206, 147, 108, 0.3);
            box-shadow: 0 8px 32px rgba(206, 147, 108, 0.1);
        }

        .settings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .setting-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
        }

        .setting-label {
            display: block;
            font-size: 0.9rem;
            color: #a0a0b0;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .setting-input {
            width: 100%;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            color: #fff;
            font-size: 1rem;
        }

        .setting-input:focus {
            outline: none;
            border-color: #ce936c;
        }

        .toggle-switch {
            position: relative;
            width: 50px;
            height: 26px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 13px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .toggle-switch.active {
            background: #ce936c;
        }

        .toggle-slider {
            position: absolute;
            top: 3px;
            left: 3px;
            width: 20px;
            height: 20px;
            background: #fff;
            border-radius: 50%;
            transition: all 0.3s ease;
        }

        .toggle-switch.active .toggle-slider {
            left: 27px;
        }

        .file-upload-wrapper {
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 60px 20px;
            border: 2px dashed rgba(206, 147, 108, 0.3);
            border-radius: 12px;
            background: rgba(0, 0, 0, 0.2);
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .file-upload-wrapper:hover {
            border-color: rgba(206, 147, 108, 0.6);
            background: rgba(206, 147, 108, 0.05);
        }

        .file-upload-wrapper.dragover {
            border-color: #ce936c;
            background: rgba(206, 147, 108, 0.1);
            transform: scale(1.02);
        }

        .upload-icon {
            font-size: 3rem;
            margin-bottom: 20px;
            opacity: 0.7;
        }

        .file-input {
            display: none;
        }

        .file-label {
            font-size: 1.1rem;
            color: #fff;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .file-hint {
            font-size: 0.9rem;
            color: #a0a0b0;
        }

        .selected-file {
            margin-top: 20px;
            padding: 15px;
            background: rgba(206, 147, 108, 0.1);
            border-radius: 8px;
            color: #ce936c;
            display: none;
        }

        .btn {
            background: linear-gradient(135deg, #ce936c 0%, #b87a56 100%);
            color: #fff;
            border: none;
            padding: 14px 32px;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
            width: 100%;
            max-width: 300px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(206, 147, 108, 0.3);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            background: rgba(255, 255, 255, 0.1);
            cursor: not-allowed;
            transform: none;
        }

        .btn-secondary {
            background: transparent;
            border: 2px solid rgba(206, 147, 108, 0.5);
            color: #ce936c;
        }

        .btn-secondary:hover {
            background: rgba(206, 147, 108, 0.1);
            border-color: #ce936c;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }

        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #ce936c;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 20px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ce936c, #b87a56);
            width: 0%;
            transition: width 0.3s ease;
        }

        .results-section {
            display: none;
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            border-color: rgba(206, 147, 108, 0.3);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }

        .stat-label {
            font-size: 0.85rem;
            color: #a0a0b0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #ce936c;
            margin-bottom: 4px;
        }

        .stat-description {
            font-size: 0.9rem;
            color: #c0c0d0;
        }

        .chart-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px;
            margin-top: 20px;
        }

        .chart-container h3 {
            font-size: 1.2rem;
            margin-bottom: 16px;
            color: #fff;
            font-weight: 600;
        }

        .chart-container img {
            width: 100%;
            border-radius: 8px;
        }

        .frame-preview {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px;
            margin-top: 20px;
        }

        .frame-preview h3 {
            font-size: 1.2rem;
            margin-bottom: 16px;
            color: #fff;
            font-weight: 600;
        }

        .frame-preview img {
            width: 100%;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 40px;
            padding: 20px 0;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.3s ease;
        }

        .feature-card:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(206, 147, 108, 0.2);
            transform: translateY(-4px);
        }

        .feature-icon {
            font-size: 2rem;
            margin-bottom: 12px;
        }

        .feature-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 8px;
        }

        .feature-desc {
            font-size: 0.9rem;
            color: #a0a0b0;
            line-height: 1.5;
        }

        .error-message {
            background: rgba(255, 59, 48, 0.1);
            border: 1px solid rgba(255, 59, 48, 0.3);
            color: #ff6b6b;
            padding: 16px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }

        .comparison-view {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .comparison-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
        }

        .comparison-item img {
            width: 100%;
            border-radius: 8px;
            margin-bottom: 12px;
        }

        .comparison-label {
            font-size: 0.9rem;
            color: #a0a0b0;
            text-align: center;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem;
            }
            
            .upload-section {
                padding: 24px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }

            .tabs {
                overflow-x: auto;
                flex-wrap: nowrap;
            }

            .action-buttons {
                flex-direction: column;
            }

            .btn {
                max-width: 100%;
            }
        }

        /* Prevent context menu and text selection */
        img {
            pointer-events: none;
        }
    </style>
</head>
<body oncontextmenu="return false;">
    <div class="watermark">© 2025 Khan Mohd Asim</div>
    
    <div class="container">
        <div class="header">
            <h1>🎬 Video Analytics AI</h1>
            <p class="subtitle">Advanced face detection and video analysis powered by computer vision</p>
            <div class="developer-badge">👨‍💻 Developed by KHAN MOHD ASIM</div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('analyze', this)">📊 Analyze</button>
            <button class="tab" onclick="switchTab('settings', this)">⚙️ Settings</button>
            <button class="tab" onclick="switchTab('history', this)">📝 History</button>
            <button class="tab" onclick="switchTab('about', this)">ℹ️ About</button>
        </div>


        <div id="analyzeTab" class="tab-content active">
            <div class="upload-section" id="uploadSection">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="file-upload-wrapper" id="dropZone">
                        <div class="upload-icon">📹</div>
                        <div class="file-label">Drop your video here or click to browse</div>
                        <div class="file-hint">Supports MP4, AVI, MOV (Max 100MB)</div>
                        <input type="file" name="video" id="videoInput" class="file-input" accept="video/*" required>
                        <div class="selected-file" id="selectedFile"></div>
                    </div>
                    <button type="submit" class="btn" id="analyzeBtn" disabled>Analyze Video</button>
                    <div class="progress-bar" id="progressBar" style="display:none;">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </form>
                <div class="error-message" id="errorMessage"></div>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="color: #a0a0b0; font-size: 1.1rem;">Analyzing your video... This may take a moment</p>
                <p style="color: #7a7a8a; font-size: 0.9rem; margin-top: 10px;" id="loadingStatus">Processing frames...</p>
            </div>

            <div class="results-section" id="resultsSection">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Faces Detected</div>
                        <div class="stat-value" id="totalFaces">0</div>
                        <div class="stat-description">Across all frames</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Average Per Frame</div>
                        <div class="stat-value" id="avgFaces">0.0</div>
                        <div class="stat-description">Face density metric</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Frames Processed</div>
                        <div class="stat-value" id="frameCount">0</div>
                        <div class="stat-description">Total video frames</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Detection Rate</div>
                        <div class="stat-value" id="detectionRate">0%</div>
                        <div class="stat-description">Frames with faces</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Max Faces/Frame</div>
                        <div class="stat-value" id="maxFaces">0</div>
                        <div class="stat-description">Peak detection</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Video Duration</div>
                        <div class="stat-value" id="duration">0s</div>
                        <div class="stat-description">Total length</div>
                    </div>
                </div>

                <div class="chart-container" id="chartContainer" style="display:none;">
                    <h3>📈 Face Detection Timeline</h3>
                    <img id="chartImage" src="" alt="Detection chart">
                </div>

                <div class="frame-preview">
                    <h3>📸 Sample Frame with Detected Faces</h3>
                    <img id="sampleFrame" src="" alt="Sample frame">
                </div>

                <div class="comparison-view" id="comparisonView" style="display:none;">
                    <div class="comparison-item">
                        <img id="beforeFrame" src="" alt="Before">
                        <div class="comparison-label">Before Detection</div>
                    </div>
                    <div class="comparison-item">
                        <img id="afterFrame" src="" alt="After">
                        <div class="comparison-label">After Detection</div>
                    </div>
                </div>

                <div class="action-buttons">
                    <button class="btn" onclick="resetForm()">Analyze Another Video</button>
                    <button class="btn btn-secondary" onclick="downloadReport()">📥 Download Report</button>
                    <button class="btn btn-secondary" onclick="exportData()">📊 Export Data</button>
                </div>
            </div>

            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-title">Accurate Detection</div>
                    <div class="feature-desc">Uses advanced Haar Cascade classifiers for reliable face detection</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-title">Fast Processing</div>
                    <div class="feature-desc">Optimized algorithms process videos efficiently</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Detailed Analytics</div>
                    <div class="feature-desc">Get comprehensive statistics and visualizations</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <div class="feature-title">Privacy First</div>
                    <div class="feature-desc">Videos are processed locally and deleted immediately</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📈</div>
                    <div class="feature-title">Timeline Charts</div>
                    <div class="feature-desc">Visualize face detection across video timeline</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💾</div>
                    <div class="feature-title">Export Options</div>
                    <div class="feature-desc">Download reports and export data in multiple formats</div>
                </div>
            </div>
        </div>


        <div id="settingsTab" class="tab-content">
            <div class="upload-section">
                <h2 style="margin-bottom: 24px; color: #fff;">Detection Settings</h2>
                <div class="settings-grid">
                    <div class="setting-card">
                        <label class="setting-label">Sensitivity Level</label>
                        <input type="range" class="setting-input" id="sensitivity" min="1" max="10" value="5">
                        <div style="color: #ce936c; margin-top: 8px; text-align: center;" id="sensitivityValue">5</div>
                    </div>
                    <div class="setting-card">
                        <label class="setting-label">Min Face Size (px)</label>
                        <input type="number" class="setting-input" id="minFaceSize" value="30" min="20" max="100">
                    </div>
                    <div class="setting-card">
                        <label class="setting-label">Frame Skip</label>
                        <input type="number" class="setting-input" id="frameSkip" value="1" min="1" max="10">
                        <div style="color: #a0a0b0; font-size: 0.8rem; margin-top: 4px;">Process every Nth frame</div>
                    </div>
                    <div class="setting-card">
                        <label class="setting-label">Draw Bounding Boxes</label>
                        <div class="toggle-switch active" id="boundingBoxToggle" onclick="toggleSetting(this)">
                            <div class="toggle-slider"></div>
                        </div>
                    </div>
                    <div class="setting-card">
                        <label class="setting-label">Generate Timeline Chart</label>
                        <div class="toggle-switch active" id="chartToggle" onclick="toggleSetting(this)">
                            <div class="toggle-slider"></div>
                        </div>
                    </div>
                    <div class="setting-card">
                        <label class="setting-label">Save Analysis History</label>
                        <div class="toggle-switch active" id="historyToggle" onclick="toggleSetting(this)">
                            <div class="toggle-slider"></div>
                        </div>
                    </div>
                </div>
                <button class="btn" onclick="saveSettings()">💾 Save Settings</button>
            </div>
        </div>


        <div id="historyTab" class="tab-content">
            <div class="upload-section">
                <h2 style="margin-bottom: 24px; color: #fff;">Analysis History</h2>
                <div id="historyList">
                    <p style="color: #a0a0b0; text-align: center; padding: 40px;">No analysis history yet. Start by analyzing a video!</p>
                </div>
            </div>
        </div>


        <div id="aboutTab" class="tab-content">
            <div class="upload-section">
                <h2 style="margin-bottom: 24px; color: #fff;">About Video Analytics AI</h2>
                <div style="color: #c0c0d0; line-height: 1.8;">
                    <p style="margin-bottom: 16px;"><strong style="color: #ce936c;">Version:</strong> 2.0.0</p>
                    <p style="margin-bottom: 16px;"><strong style="color: #ce936c;">Developer:</strong> Khan Mohd Asim</p>
                    <p style="margin-bottom: 16px;"><strong style="color: #ce936c;">Copyright:</strong> © 2025 Khan Mohd Asim. All rights reserved.</p>
                    <p style="margin-bottom: 16px;"><strong style="color: #ce936c;">Technology Stack:</strong> Flask, OpenCV, Python, Computer Vision</p>
                    <p style="margin-bottom: 24px;">This advanced video analytics platform uses state-of-the-art computer vision algorithms to detect and analyze faces in video content. Built with privacy and accuracy in mind.</p>
                    
                    <div style="background: rgba(206, 147, 108, 0.1); border-left: 3px solid #ce936c; padding: 16px; border-radius: 8px; margin-top: 24px;">
                        <strong style="color: #ce936c;">⚠️ Legal Notice:</strong>
                        <p style="margin-top: 8px; font-size: 0.9rem;">Unauthorized copying, modification, or distribution of this software is strictly prohibited. This software is protected by copyright law.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>

        document.addEventListener('keydown', function(e) {
            if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I') || 
                (e.ctrlKey && e.shiftKey && e.key === 'J') || (e.ctrlKey && e.key === 'U')) {
                e.preventDefault();
                return false;
            }
        });


        let settings = {
            sensitivity: 5,
            minFaceSize: 30,
            frameSkip: 1,
            boundingBox: true,
            chart: true,
            history: true
        };


        if (localStorage.getItem('videoAnalyticsSettings')) {
            settings = JSON.parse(localStorage.getItem('videoAnalyticsSettings'));
        }

        document.getElementById('sensitivity').addEventListener('input', function(e) {
            document.getElementById('sensitivityValue').textContent = e.target.value;
        });

        const dropZone = document.getElementById('dropZone');
        const videoInput = document.getElementById('videoInput');
        const selectedFile = document.getElementById('selectedFile');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const uploadForm = document.getElementById('uploadForm');
        const uploadSection = document.getElementById('uploadSection');
        const loading = document.getElementById('loading');
        const resultsSection = document.getElementById('resultsSection');
        const errorMessage = document.getElementById('errorMessage');
        const progressBar = document.getElementById('progressBar');
        const progressFill = document.getElementById('progressFill');

        let currentResults = null;


        function switchTab(tabName, element) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            if (element) {
                element.classList.add('active');
            } else {
                document.querySelector(`.tab[onclick="switchTab('${tabName}', this)"]`).classList.add('active');
            }
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            if (tabName === 'history') {
                loadHistory();
            }
        }


        function toggleSetting(element) {
            element.classList.toggle('active');
        }


        function saveSettings() {
            settings = {
                sensitivity: parseInt(document.getElementById('sensitivity').value),
                minFaceSize: parseInt(document.getElementById('minFaceSize').value),
                frameSkip: parseInt(document.getElementById('frameSkip').value),
                boundingBox: document.getElementById('boundingBoxToggle').classList.contains('active'),
                chart: document.getElementById('chartToggle').classList.contains('active'),
                history: document.getElementById('historyToggle').classList.contains('active')
            };
            localStorage.setItem('videoAnalyticsSettings', JSON.stringify(settings));
            alert('✓ Settings saved successfully!');
        }

  
        dropZone.addEventListener('click', () => videoInput.click());


        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                videoInput.files = files;
                handleFileSelect();
            }
        });

        videoInput.addEventListener('change', handleFileSelect);

        function handleFileSelect() {
            const file = videoInput.files[0];
            if (file) {
                const fileSize = (file.size / (1024 * 1024)).toFixed(2);
                if (fileSize > 100) {
                    showError('File size exceeds 100MB limit');
                    videoInput.value = '';
                    return;
                }
                selectedFile.textContent = `📹 ${file.name} (${fileSize} MB)`;
                selectedFile.style.display = 'block';
                analyzeBtn.disabled = false;
                errorMessage.style.display = 'none';
            }
        }


        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(uploadForm);
            formData.append('settings', JSON.stringify(settings));
            
            uploadSection.style.display = 'none';
            loading.style.display = 'block';
            resultsSection.style.display = 'none';
            progressBar.style.display = 'block';
            

            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;
                progressFill.style.width = progress + '%';
            }, 500);
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'X-License-Key': 'KHAN_MOHD_ASIM_2025'
                    },
                    body: formData
                });
                
                clearInterval(progressInterval);
                progressFill.style.width = '100%';
                
                if (!response.ok) {
                    throw new Error('Analysis failed');
                }
                
                const data = await response.json();
                if (data.error) {
                    throw new Error(data.error);
                }
                currentResults = data;
                displayResults(data);
                
                if (settings.history) {
                    saveToHistory(data);
                }
            } catch (error) {
                clearInterval(progressInterval);
                showError('Failed to analyze video: ' + error.message);
                uploadSection.style.display = 'block';
            } finally {
                loading.style.display = 'none';
                setTimeout(() => {
                    progressBar.style.display = 'none';
                    progressFill.style.width = '0%';
                }, 1000);
            }
        });

        function displayResults(data) {
            document.getElementById('totalFaces').textContent = data.total_faces;
            document.getElementById('avgFaces').textContent = data.avg_faces;
            document.getElementById('frameCount').textContent = data.frame_count;
            document.getElementById('detectionRate').textContent = data.detection_rate + '%';
            document.getElementById('maxFaces').textContent = data.max_faces || 0;
            document.getElementById('duration').textContent = data.duration || '0s';
            
            if (data.sample_frame) {
                document.getElementById('sampleFrame').src = 'data:image/jpeg;base64,' + data.sample_frame;
            }

            if (data.chart && settings.chart) {
                document.getElementById('chartContainer').style.display = 'block';
                document.getElementById('chartImage').src = 'data:image/png;base64,' + data.chart;
            }

            if (data.before_frame && data.after_frame) {
                document.getElementById('comparisonView').style.display = 'grid';
                document.getElementById('beforeFrame').src = 'data:image/jpeg;base64,' + data.before_frame;
                document.getElementById('afterFrame').src = 'data:image/jpeg;base64,' + data.after_frame;
            }
            
            resultsSection.style.display = 'block';
        }

        function showError(message) {
            errorMessage.textContent = '⚠️ ' + message;
            errorMessage.style.display = 'block';
        }

        function resetForm() {
            uploadForm.reset();
            selectedFile.style.display = 'none';
            analyzeBtn.disabled = true;
            resultsSection.style.display = 'none';
            uploadSection.style.display = 'block';
            errorMessage.style.display = 'none';
            document.getElementById('chartContainer').style.display = 'none';
            document.getElementById('comparisonView').style.display = 'none';
        }

        function downloadReport() {
            if (!currentResults) return;
            
            const report = `VIDEO ANALYTICS REPORT
Generated by: Khan Mohd Asim Video Analytics AI
Date: ${new Date().toLocaleString()}
═══════════════════════════════════════

DETECTION STATISTICS
─────────────────────────────────────
Total Faces Detected: ${currentResults.total_faces}
Average Faces per Frame: ${currentResults.avg_faces}
Total Frames Processed: ${currentResults.frame_count}
Detection Rate: ${currentResults.detection_rate}%
Maximum Faces in Single Frame: ${currentResults.max_faces || 0}
Video Duration: ${currentResults.duration || 'N/A'}

═══════════════════════════════════════
Copyright © 2025 Khan Mohd Asim
All Rights Reserved
`;
            
            const blob = new Blob([report], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `video_analysis_report_${Date.now()}.txt`;
            a.click();
            window.URL.revokeObjectURL(url);
        }

        function exportData() {
            if (!currentResults) return;
            
            const jsonData = JSON.stringify(currentResults, null, 2);
            const blob = new Blob([jsonData], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `video_analysis_data_${Date.now()}.json`;
            a.click();
            window.URL.revokeObjectURL(url);
        }

        function saveToHistory(data) {
            let history = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
            history.unshift({
                timestamp: new Date().toISOString(),
                results: data
            });
            if (history.length > 10) history = history.slice(0, 10);
            localStorage.setItem('analysisHistory', JSON.stringify(history));
        }

        function loadHistory() {
            const history = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
            const historyList = document.getElementById('historyList');
            
            if (history.length === 0) {
                historyList.innerHTML = '<p style="color: #a0a0b0; text-align: center; padding: 40px;">No analysis history yet. Start by analyzing a video!</p>';
                return;
            }
            
            historyList.innerHTML = history.map((item, index) => `
                <div class="stat-card" style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <div class="stat-label">Analysis #${history.length - index}</div>
                            <div style="color: #a0a0b0; font-size: 0.85rem;">${new Date(item.timestamp).toLocaleString()}</div>
                        </div>
                        <button class="btn btn-secondary" style="padding: 8px 16px; font-size: 0.85rem; margin: 0;" onclick="deleteHistory(${index})">🗑️</button>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px;">
                        <div>
                            <div style="color: #a0a0b0; font-size: 0.8rem;">Total Faces</div>
                            <div style="color: #ce936c; font-size: 1.2rem; font-weight: 600;">${item.results.total_faces}</div>
                        </div>
                        <div>
                            <div style="color: #a0a0b0; font-size: 0.8rem;">Avg/Frame</div>
                            <div style="color: #ce936c; font-size: 1.2rem; font-weight: 600;">${item.results.avg_faces}</div>
                        </div>
                        <div>
                            <div style="color: #a0a0b0; font-size: 0.8rem;">Frames</div>
                            <div style="color: #ce936c; font-size: 1.2rem; font-weight: 600;">${item.results.frame_count}</div>
                        </div>
                        <div>
                            <div style="color: #a0a0b0; font-size: 0.8rem;">Rate</div>
                            <div style="color: #ce936c; font-size: 1.2rem; font-weight: 600;">${item.results.detection_rate}%</div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function deleteHistory(index) {
            let history = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
            history.splice(index, 1);
            localStorage.setItem('analysisHistory', JSON.stringify(history));
            loadHistory();
        }


        document.addEventListener('DOMContentLoaded', function() {

            if (settings) {
                document.getElementById('sensitivity').value = settings.sensitivity;
                document.getElementById('sensitivityValue').textContent = settings.sensitivity;
                document.getElementById('minFaceSize').value = settings.minFaceSize;
                document.getElementById('frameSkip').value = settings.frameSkip;
                
                if (!settings.boundingBox) document.getElementById('boundingBoxToggle').classList.remove('active');
                if (!settings.chart) document.getElementById('chartToggle').classList.remove('active');
                if (!settings.history) document.getElementById('historyToggle').classList.remove('active');
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
@check_license
def analyze():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video uploaded'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        

        file.seek(0, os.SEEK_END)
        file_size = file.tell() / (1024 * 1024)  
        file.seek(0) 
        if file_size > 100:
            return jsonify({'error': 'File size exceeds 100MB limit'}), 400
        

        allowed_extensions = {'.mp4', '.avi', '.mov'}
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return jsonify({'error': 'Unsupported file format'}), 400
        

        settings_json = request.form.get('settings', '{}')
        settings = json.loads(settings_json)
        

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = f'temp_video_{timestamp}.mp4'
        file.save(filepath)
        

        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return jsonify({'error': 'Failed to open video file'}), 400
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 1000:  
            cap.release()
            return jsonify({'error': 'Video too long for free tier'}), 400
        duration = round(total_frames / fps if fps > 0 else 0, 2)
        
        total_faces = 0
        frame_count = 0
        frames_with_faces = 0
        max_faces = 0
        sample_frame_b64 = None
        before_frame_b64 = None
        after_frame_b64 = None
        face_timeline = []
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            return jsonify({'error': 'Failed to load face detection model'}), 500
        
        frame_skip = settings.get('frameSkip', 1)
        min_face_size = settings.get('minFaceSize', 30)
        draw_boxes = settings.get('boundingBox', True)
        
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_idx += 1
            if frame_idx % frame_skip != 0:
                continue
                
            frame_count += 1
            

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1 + (settings.get('sensitivity', 5) / 50.0), 
                minNeighbors=5, 
                minSize=(min_face_size, min_face_size)
            )
            
            num_faces = len(faces)
            face_timeline.append(num_faces)
            
            if num_faces > 0:
                frames_with_faces += 1
                total_faces += num_faces
                max_faces = max(max_faces, num_faces)
                

                if before_frame_b64 is None:
                    _, buffer = cv2.imencode('.jpg', frame)
                    before_frame_b64 = base64.b64encode(buffer).decode('utf-8')
                

                if draw_boxes and sample_frame_b64 is None:
                    frame_with_boxes = frame.copy()
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame_with_boxes, (x, y), (x+w, y+h), (206, 147, 108), 3)
                        cv2.putText(frame_with_boxes, 'Face', (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (206, 147, 108), 2)
                    
                    _, buffer = cv2.imencode('.jpg', frame_with_boxes)
                    sample_frame_b64 = base64.b64encode(buffer).decode('utf-8')
                    
                    if after_frame_b64 is None:
                        after_frame_b64 = sample_frame_b64
        
        cap.release()
        

        chart_b64 = None
        if settings.get('chart', True) and len(face_timeline) > 0:
            plt.figure(figsize=(12, 4), facecolor='#1a1a2e')
            ax = plt.gca()
            ax.set_facecolor('#1a1a2e')
            
            plt.plot(face_timeline, color='#ce936c', linewidth=2)
            plt.fill_between(range(len(face_timeline)), face_timeline, alpha=0.3, color='#ce936c')
            plt.xlabel('Frame Number', color='#a0a0b0')
            plt.ylabel('Faces Detected', color='#a0a0b0')
            plt.title('Face Detection Timeline', color='#ffffff', fontsize=14, pad=20)
            plt.grid(True, alpha=0.1, color='#ffffff')
            ax.spines['bottom'].set_color('#a0a0b0')
            ax.spines['top'].set_color('#a0a0b0')
            ax.spines['left'].set_color('#a0a0b0')
            ax.spines['right'].set_color('#a0a0b0')
            ax.tick_params(colors='#a0a0b0')
            
            with io.BytesIO() as buffer:
                plt.savefig(buffer, format='png', bbox_inches='tight', facecolor='#1a1a2e')
                buffer.seek(0)
                chart_b64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close('all')  
        

        try:
            os.remove(filepath)
        except:
            pass
        

        avg_faces = round(total_faces / frame_count, 2) if frame_count > 0 else 0
        detection_rate = round((frames_with_faces / frame_count * 100), 1) if frame_count > 0 else 0
        
        results = {
            'total_faces': total_faces,
            'avg_faces': avg_faces,
            'frame_count': frame_count,
            'detection_rate': detection_rate,
            'max_faces': max_faces,
            'duration': f"{duration}s",
            'sample_frame': sample_frame_b64,
            'before_frame': before_frame_b64,
            'after_frame': after_frame_b64,
            'chart': chart_b64,
            'frames_with_faces': frames_with_faces,
            'timestamp': datetime.now().isoformat(),
            'developer': 'Khan Mohd Asim'
        }
        
        return jsonify(results)
    
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Video Analytics AI Platform")
    print("Developer: KHAN MOHD_ASIM")
    print("Copyright © 2025. All Rights Reserved.")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
Video Analytics AI Platform
Developer: KHAN MOHD ASIM
Copyright (c) 2025. All rights reserved.
Unauthorized copying, distribution, or modification is strictly prohibited.
"""