<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Hybrid OCR & Manual Entry Tool</title>

    <!-- Handsontable CSS and JS from CDN -->
    <link rel="stylesheet" type="text/css"
        href="https://cdn.jsdelivr.net/npm/handsontable@12.1.0/dist/handsontable.full.min.css" />
    <script src="https://cdn.jsdelivr.net/npm/handsontable@12.1.0/dist/handsontable.full.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/string-similarity@4.0.4/umd/string-similarity.min.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/hyperformula@2.6.2/dist/hyperformula.full.min.js"></script>

    <style>
        /* --------------------- Global & Container Styles --------------------- */
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            overflow: hidden;
            /* Prevent body scroll */
        }

        #hybrid-tool-container {
            width: 100%;
            max-width: 100%;
            /* reduced to allow Handsontable padding */
            max-height: 758px;
            background-color: #0a0a0a;
            padding: 0 24px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            /* Prevent horizontal scroll on container */
        }

        #main-container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        /* --------------------- Top Row Controls --------------------- */
        #top-row-controls {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-top: 16px;
            margin-bottom: 16px;
        }

        #tool-heading {
            font-size: 16px;
            font-weight: 500;
            color: #ffffff;
        }

        #top-row-right {
            display: flex;
            gap: 12px;
        }

        /* --------------------- Table Action Buttons --------------------- */
        #table-action-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-bottom: 8px;
        }

        #table-action-buttons button {
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            font-size: 14px;
            cursor: pointer;
        }

        #extract-btn {
            background-color: #2b2a2a;
            color: #fff;
        }

        #submit-btn {
            background-color: #D99E01;
            color: #fff;
            font-weight: 700;
        }

        /* ---------- --- Upload area as Heading Row--- ------  */
        /* Just override for header-row */
        .upload-row.header-row {
            grid-template-columns: 40px 1fr 1fr 1fr 1fr 1fr !important;
            /* 6 columns instead of 4 */
            gap: 2px !important;
        }


        /* --------------------- Table & OCR Wrapper --------------------- */
        #table-and-ocr-wrapper {
            display: flex;
            flex: 1;
            overflow: visible;
        }

        /* --------------------- Handsontable Area --------------------- */
        #handsontable-container {
            max-height: none;
            height: 500px;
            overflow-y: auto;
            overflow-x: auto;
            flex: 1 1 auto;
            min-width: 0;
            margin-right: 16px;
        }

        #hot {
            width: 100%;
            height: auto;
            max-height: none;
        }

        /* Override cell borders to #444 */
        #handsontable-container .wtBorder:not(.current) {
            border-color: #444 !important;
        }

        /* Remove the conflicting general rules and use only specific ones */

        .handsontable th .ocr-upload-area-header {
            height: 40px !important;
            min-height: 40px !important;
            padding: 4px 4px !important;
            box-sizing: border-box !important;
            font-size: 12px !important;
            /* Use grid instead of flex */
            display: grid !important;
            grid-template-columns: auto auto !important;
            /* Two columns for icon and text */
            justify-content: center !important;
            /* Center the grid content */
            align-items: center !important;
            /* Center vertically */
            gap: 4px !important;
        }

        .handsontable th .ocr-upload-area-header .upload-icon {
            font-size: 16px !important;
            margin: 0 !important;
            line-height: 1 !important;
        }

        .handsontable th .ocr-upload-area-header .upload-label {
            font-size: 12px !important;
            margin: 0 !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
        }

        .handsontable th {
            vertical-align: middle !important;
            text-align: center !important;
            width: auto !important;
        }



        /* GLIDE TABLE UI and BLACK & YELLOW THEME */
        /* Selected cell border - now more specific */
        #handsontable-container .wtBorder.current {
            border-color: #D99E01 !important;
        }

        /* Black and white Handsontable theme */
        .handsontable {
            background-color: #0a0a0a !important;
            color: #ffffff !important;
        }

        /* Table cells - with textwrap functionality */
        .handsontable td {
            background-color: #0a0a0a;
            color: #ffffff !important;
            border-color: #222222 !important;

            white-space: normal !important;
            word-break: break-word !important;
            overflow-wrap: break-word !important;
            max-width: 300px;
        }

        /* Column headers */
        .handsontable .ht_clone_top th,
        .handsontable .ht_clone_top_left_corner th {
            background-color: #0a0a0a !important;
            color: #7e7e7e !important;
            border-color: #222222 !important;
        }

        /* Row headers */
        .handsontable .ht_clone_left th {
            background-color: #0a0a0a !important;
            color: #7e7e7e !important;
            border-color: #222222 !important;
        }

        /* Selected cell */
        .handsontable .current {
            background-color: #231d0f !important;
        }

        /* Target wtBorder current elements with inline background-color */
        div.wtBorder.current[style*="background-color"] {
            background-color: 1px #D99E01 !important;
        }

        /* More specific targeting */
        .handsontable div.wtBorder.current {
            background-color: 1px #D99E01 !important;
        }

        /* Target all variations */
        div.wtBorder.current,
        div.wtBorder.current.corner {
            background-color: #D99E01 !important;
        }

        /* COLUMN SELECTION */
        /* More specific targeting for column/row selections */
        .handsontable .wtBorder.area[style*="background-color"] {
            background-color: #D99E01 !important;
        }

        .handsontable td.area.highlight {
            background-color: #231d0f !important;
            /* Same as current cell */
        }

        /* Input fields when editing */
        .handsontable .handsontableInputHolder textarea.handsontableInput,
        .handsontable .handsontableInputHolder input.handsontableInput {
            background-color: #000000 !important;
            color: #ffffff !important;
            /* border: #666 !important; */
        }


        .handsontable textarea[data-hot-input]:focus {
            border: 1px solid #D99E01 !important;
            outline: none !important;
            box-shadow: none !important;
        }


        /* Dropdown menus */
        /* ========== DROPDOWN & CONTEXT MENU FIXES ========== */

        /* Context Menu Container - Most specific */
        .htContextMenu.htMenu {
            background-color: #1a1a1a !important;
            /* border: 1px solid #444 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important; */
        }

        /* Context Menu Table */
        .htContextMenu.htMenu table.htCore {
            background-color: #1a1a1a !important;
        }

        /* Context Menu Items */
        .htContextMenu.htMenu tbody tr td {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            /* padding: 8px 12px !important; */
            border: none !important;
        }

        /* Context Menu Hover State */
        .htContextMenu.htMenu tbody tr td.current,
        .htContextMenu.htMenu tbody tr:hover td {
            background-color: #2a2a2a !important;
            color: #D99E01 !important;
        }

        /* Context Menu Disabled Items */
        .htContextMenu.htMenu tbody tr td.htDisabled,
        .htContextMenu.htMenu tbody tr td.htDisabled:hover {
            background-color: #1a1a1a !important;
            color: #666 !important;
            cursor: default !important;
        }

        /* Context Menu Separators */
        .htContextMenu.htMenu .ht_sep {
            background-color: #444 !important;
            height: 1px !important;
            margin: 4px 0 !important;
        }

        .htContextMenu .ht_master table.htCore {
            border-color: #1F1F1F;
            border-style: solid;
            border-width: 1.5px;
        }

        /* Dropdown Menu Specific Fixes */
        .htDropdownMenu.htMenu {
            background-color: #1a1a1a !important;
            border: 1px solid #444 !important;
        }

        .htDropdownMenu.htMenu table.htCore {
            background-color: #1a1a1a !important;
        }

        .htDropdownMenu.htMenu tbody tr td {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
        }

        .htDropdownMenu.htMenu tbody tr:hover td {
            background-color: #2a2a2a !important;
        }

        .handsontable.listbox .ht_master table {
            border: 1px solid #1F1F1F;
            border-collapse: separate;
            /* background: #1a1a1a; */
        }

        .handsontable.listbox td {
            background-color: #1a1a1a !important;
            /* color: #323232 !important; */
            /* border-color: #333 !important; */
        }

        .handsontable.listbox tr td.current,
        .handsontable.listbox tbody tr:hover td {
            background-color: #2a2a2a !important;
            /* color: #D99E01 !important; */
        }


        /* ========== SCROLLBARS ========== */
        /* .handsontable .wtHolder::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

.handsontable .wtHolder::-webkit-scrollbar-track {
    background: #1a1a1a;
}

.handsontable .wtHolder::-webkit-scrollbar-thumb {
    background: #666;
    border-radius: 5px;
}

.handsontable .wtHolder::-webkit-scrollbar-thumb:hover {
    background: #888;
} */






        /* More specific class targeting */
        .handsontable textarea.handsontableInput,
        .handsontable input.handsontableInput {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }

        .handsontable .htCore .htEditor {
            background-color: #ffffff !important;
        }

        .handsontable .wtHolder textarea,
        .handsontable .wtHolder input {
            background: #ffffff !important;
        }

        /* Instructions bar above the table */
        .instructions {
            background: #2b2a2a;
            /* border: 1px solid #444; */
            border-radius: 6px;
            padding: 8px 12px;
            /* margin-bottom: 12px; */
            font-size: 0.8rem;
            line-height: 1.3;
            color: #ccc;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            width: fit-content;
            /* Only as wide as content */
            position: absolute;
            left: 50%;
            top: 10px;
            transform: translateX(-50%);
            /* Perfect center */
            z-index: 1;
        }

        .instructions strong {
            color: #fff;
        }

        .help-icon {
            float: right;
            cursor: pointer;
            opacity: 0.7;
            position: relative;
            top: 0;
        }

        .help-icon:hover {
            opacity: 1;
        }

        .help-popover {
            position: fixed;
            background: #fff;
            border: 2px solid #ddd;
            border-radius: 6px;
            padding: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1002;
            width: 50vw;
            max-width: none;
            min-width: none;
            margin-top: 8px;
            top: 100%;
            /* Below the help icon */
            left: 50%;
            /* Align to right edge of help icon */
            transform: translateX(-50%);
            display: none;
            color: #000;
        }

        .help-popover img {
            width: 100%;
            height: auto;
            /* Maintain aspect ratio */
            max-height: 50vh;
            /* Prevent it from getting too tall */
            object-fit: contain;
            /* Maintain aspect ratio while fitting */
            /* Remove the height restrictions I added */
        }

        /* OCR Overlay Panel Styles */
        #ocr-panel {
            position: fixed;
            top: 5%;
            left: 5vw;
            width: 90vw;
            height: 80%;
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 20px;
            box-sizing: border-box;
            overflow-y: auto;
            display: none;
            flex-direction: column;
            color: #fff;
            z-index: 1000;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
            border: 1px solid #444;
        }

        #ocr-panel.open {
            display: flex;
        }

        #ocr-panel-header {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 12px;
            position: relative;
        }

        #ocr-close-btn {
            font-size: 20px;
            cursor: pointer;
            opacity: 0.7;
        }

        #ocr-close-btn:hover {
            opacity: 1;
        }

        #ocr-panel-body {
            margin-top: 8px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .dark-label {
            font-size: 14px;
            margin-bottom: 4px;
            margin-top: 10px;
            text-align: center;
        }


        .upload-row {
            display: grid;
            grid-template-columns: 1.8fr 1fr 3.2fr 3.2fr;
            /* Part, Qty, Desc, Material */
            gap: 8px;
            width: 100%;
            box-sizing: border-box;
        }

        .upload-column {
            display: flex;
            flex-direction: column;
            gap: 6px;
            min-width: 0;
            /* Allow shrinking */
        }


        .upload-icon {
            font-size: 24px;
            color: #666;
            margin-bottom: 8px;
            transition: color 0.2s ease;
        }

        .upload-label {
            font-size: 14px;
            color: #666;
            font-weight: 500;
            transition: color 0.2s ease;
        }


        .ocr-upload-area {
            border: 1.5px dashed #555;
            border-radius: 6px;
            padding: 6px;
            text-align: center;
            background: #0a0a0a;
            color: #000;
            position: relative;
            cursor: pointer;
            min-height: 180px;
            height: auto;
            display: flex;
            flex-direction: column;
            justify-content: center;
            /* Center content when no image */
            align-items: center;
            transition: all 0.2s ease;
        }

        .ocr-upload-area:hover {
            border: 1.5px solid #D99E00 !important;
            /* Your specified color */
            background: #0a0a0a;
        }

        /* Drag over effect */
        .ocr-upload-area.drag-over {
            border-color: #D99E00;
            border-style: solid;
            background: #0a0a0a;
            /* transform: scale(1.03); */
            box-shadow: 0 4px 12px rgba(216, 147, 38, 0.2);
        }

        /* Active drag state */
        .ocr-upload-area.drag-active {
            border-color: #D99E00;
            border-width: 3px;
            background: #fff6e6;
        }

        .ocr-upload-area:hover .upload-icon,
        .ocr-upload-area:hover .upload-label,
        .ocr-upload-area.drag-over .upload-icon,
        .ocr-upload-area.drag-over .upload-label,
        .ocr-upload-area.drag-active .upload-icon .ocr-upload-area.drag-active .upload-label {
            color: #D99E00 !important;
        }


        /* Only override when file is uploaded */
        .ocr-upload-area.has-file {
            justify-content: flex-start;
            /* Move to top when file uploaded */
        }

        /* Hide upload prompt when file is uploaded */
        .ocr-upload-area.has-file .upload-icon,
        .ocr-upload-area.has-file .upload-label {
            display: none;
        }


        .upload-clear-btn {
            position: absolute;
            top: 4px;
            right: 4px;
            width: 16px;
            height: 16px;
            background: rgba(108, 117, 125, 0.8);
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 12px;
            line-height: 1;
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            opacity: 0.7;
            transition: all 0.2s ease;
            z-index: 2;
        }

        .upload-clear-btn:hover {
            background: rgb(218, 53, 51);
            transform: scale(1.1);
        }

        .ocr-upload-area.has-file .upload-clear-btn {
            display: flex;
        }

        .ocr-upload-area input[type="file"] {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
            z-index: 1;
        }

        .ocr-image-preview {
            width: 100%;
            max-height: none;
            height: auto;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            overflow: hidden;
            background-color: #222;
            margin-top: 6px;
        }

        .ocr-image-preview img {
            max-width: 100%;
            height: auto;
            display: block;
        }

        .file-status {
            font-size: 0.75rem;
            font-weight: bold;
            margin-top: 1px;
            color: #D99E00;
            display: none;
        }

        .ocr-upload-area.has-file .file-status {
            display: block;
        }


        #ocr-process-btn {
            background-color: #D99E00;
            color: #fff;
            border: none;
            border-radius: 4px;
            padding: 8px 12px;
            cursor: pointer;
        }

        #ocr-process-btn:disabled {
            background-color: #444;
            cursor: not-allowed;
        }

        /* Low similarity warning for dropdown cells */
        .low-similarity-cell {
            background-color: a(255, 193, 7, 0.3) !important;
            /* Yellow warning background */
            border: 1px solid #ffc107 !important;
            position: relative;
        }

        /* Warning icon for low similarity cells */
        .low-similarity-cell::after {
            content: "⚠️";
            position: absolute;
            top: 2px;
            right: 2px;
            font-size: 12px;
            z-index: 10;
            pointer-events: none;
        }


        /* Warning icon for potential missing childparts */
        .needs-review-cell {
            position: relative;
        }

        .needs-review-cell::after {
            content: "⚠️";
            position: absolute;
            top: 2px;
            right: 2px;
            font-size: 12px;
            z-index: 10;
            cursor: pointer;
            opacity: 0.8;
            pointer-events: auto;
        }

        .needs-review-cell::after:hover {
            opacity: 1;
            transform: scale(1.1);
        }

        /* Warning popup */
        .warning-popup {
            position: fixed;
            background: #1a1a1a47;
            border-radius: 6px;
            padding: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 1003;
            color: #fff;
            max-width: 300px;
            display: none;
        }

        .warning-popup h5 {
            margin: 0 0 8px 0;
            color: #ffc107;
        }

        .warning-popup p {
            margin: 0 0 8px 0;
            font-size: 14px;
        }

        .warning-popup button {
            background: #D89326;
            color: #fff;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }

        /* --------------------- Responsive Behavior --------------------- */
        @media (max-width: 960px) {
            #table-and-ocr-wrapper {
                flex-direction: column;
            }

            /* Responsive positioning for #ocr-panel removed */
            #handsontable-container {
                margin-right: 0;
            }

            #top-row-right {
                flex-wrap: wrap;
                gap: 8px;
            }

            #top-row-right button {
                width: 100%;
            }
        }
    </style>
</head>

<body>
    <div id="hybrid-tool-container">
        <div id="main-container">
            <!-- Top Row Controls -->
            <div id="top-row-controls">
                <!-- <div id="top-row-left">
          <span id="tool-heading">Add child parts/BO</span>
        </div> -->
                <!-- #top-row-right removed -->
            </div>

            <!-- Table and OCR Panel Wrapper -->
            <div id="table-and-ocr-wrapper">
                <!-- Handsontable Area (Left) -->
                <div id="handsontable-container">


                    <div id="table-action-buttons">
                        <button id="extract-btn">Extract</button>
                        <button id="submit-btn">Submit</button>
                    </div>

                    <!-- Removed the Header -->
                    <!-- Handsontable placeholder (will be initialized via JS) -->
                    <div id="hot"></div>
                </div>

                <!-- OCR Slide-In Panel (Right) -->
                <div id="ocr-panel">
                    <div id="ocr-panel-header">
                        <span id="ocr-close-btn">×</span>
                    </div>
                    <!-- Instructions bar above the table -->
                    <div class="instructions">
                        🔢 &lt; 20 rows | 🔍 zoom &amp; sharp | 🚫 no header
                        <span id="help-icon" class="help-icon"><i data-lucide="info"></i></span>
                        <div id="help-popover" class="help-popover">
                            <strong>Good vs Bad Screenshot:</strong><br />
                            <img src="sample-screenshot.png" style="width: 100%;" />
                        </div>
                    </div>


                    <div id="ocr-panel-body">
                        <div class="upload-row">
                            <div class="upload-column">
                                <label class="dark-label">Part Number</label>
                                <div class="ocr-upload-area" data-column="Part Number">
                                    <div class="upload-icon"><i data-lucide="upload"></i></div>
                                    <!-- <div class="upload-label">Upload Image</div> -->
                                    <button class="upload-clear-btn" onclick="clearUpload(this, event)">×</button>
                                    <input type="file" accept="image/*" />
                                    <div class="file-status">✓ Uploaded</div>
                                    <div class="ocr-image-preview"></div>
                                </div>
                            </div>
                            <div class="upload-column">
                                <label class="dark-label">Quantity</label>
                                <div class="ocr-upload-area" data-column="Quantity">
                                    <div class="upload-icon"><i data-lucide="upload"></i></div>
                                    <!-- <div class="upload-label">Upload Image</div> -->
                                    <button class="upload-clear-btn" onclick="clearUpload(this, event)">×</button>
                                    <input type="file" accept="image/*" />
                                    <div class="file-status">✓ Uploaded</div>
                                    <div class="ocr-image-preview"></div>
                                </div>
                            </div>
                            <div class="upload-column">
                                <label class="dark-label">Description</label>
                                <div class="ocr-upload-area" data-column="Description">
                                    <div class="upload-icon"><i data-lucide="upload"></i></div>
                                    <!-- <div class="upload-label">Upload Image</div> -->
                                    <button class="upload-clear-btn" onclick="clearUpload(this, event)">×</button>
                                    <input type="file" accept="image/*" />
                                    <div class="file-status">✓ Uploaded</div>
                                    <div class="ocr-image-preview"></div>
                                </div>
                            </div>
                            <div class="upload-column">
                                <label class="dark-label">Material</label>
                                <div class="ocr-upload-area" data-column="Material">
                                    <div class="upload-icon"><i data-lucide="upload"></i></div>
                                    <!-- <div class="upload-label">Upload Image</div> -->
                                    <button class="upload-clear-btn" onclick="clearUpload(this, event)">×</button>
                                    <input type="file" accept="image/*" />
                                    <div class="file-status">✓ Uploaded</div>
                                    <div class="ocr-image-preview"></div>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: flex-end; margin-top: 16px;">
                            <button id="ocr-process-btn" disabled>Process</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ——— Begin Existing JavaScript Logic ——— -->
    <!-- (These <script> blocks are your original logic, left completely intact. 
       They include renderSpreadsheet(), addColumn(), sendDataToBackend(), OCR calls, etc.) -->

    <script>
        // ─────────────────────────────────────────────────────────────────────
        // Global state & utility functions (unchanged from your original)
        // ─────────────────────────────────────────────────────────────────────
        let currentStep = 1; // (unused now that we've collapsed Step 1/2 into one hybrid view)
        // Column‐to‐Title mapping (used by renderSpreadsheet)
        const COLUMN_TITLES = {
            PartNumber: "Part Number",
            Quantity: "Quantity",
            Description: "Description",
            Material: "Material",
            "Matched Childpart": "Part Number: Child Part/BO",
            Type: "Type",
        };

        let spreadsheetData = [];
        let columnsList = [];
        let hot;
        let windowChildParts = []; // expose on window for debugging
        let _cutBackup = [];

        // Fetch query-params (project, part, parentdrgnum) on load and fetch childParts
        window.addEventListener("DOMContentLoaded", async () => {
            const urlParams = new URLSearchParams(window.location.search);
            const project = urlParams.get("project");
            const partNumber = urlParams.get("part");
            const parentDrgNum = urlParams.get("parentdrgnum");
            if (!project || !partNumber || !parentDrgNum) {
                alert("Missing required query params: project/part/parentdrgnum");
                // Do not return; always initialize table even if params are missing
            } else {
                try {
                    const resp = await fetch(
                        "https://ocr-table-extractor.onrender.com/fetch-drawings",
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ project, part: partNumber }),
                        }
                    );
                    const data = await resp.json();
                    windowChildParts = data.rows.map((r) =>
                        decodeURIComponent(r.drawingNumber || "")
                    );
                    console.log("✅ Decoded Part Numbers:", windowChildParts);
                } catch (err) {
                    console.error("Error fetching drawing data:", err);
                    windowChildParts = []; // Fallback to empty array
                }
            }
            // Always initialize Handsontable, even if fetch fails or params are missing
            initializeHandsontable();
        });

        // Sequential character matching + best‐match utility
        function sequentialCharacterMatch(part, child) {
            if (!part || !child) return 0;
            const p = part.trim().toUpperCase();
            const c = child.trim().toUpperCase();
            if (p === c) return 1.0;
            if (c.includes(p)) return 0.99;
            let i = 0,
                j = 0,
                matched = 0;
            while (i < p.length && j < c.length) {
                if (p[i] === c[j]) {
                    matched++;
                    i++;
                }
                j++;
            }
            const baseSim = matched / p.length;
            const lengthDiff = Math.abs(p.length - c.length);
            const penalty = lengthDiff > 1 ? (lengthDiff - 1) * 0.1 : 0;
            const sim = Math.max(0, baseSim - penalty);
            if (matched === p.length) return Math.max(0.85, sim);
            return sim;
        }

        function findBestSequentialMatch(partText, drawingNumbers) {
            if (!partText || !drawingNumbers.length || !drawingNumbers.length) {
                return { bestMatch: { target: "", rating: 0 }, allMatches: [] };
            }
            const matches = drawingNumbers.map((d) => ({
                target: d,
                rating: sequentialCharacterMatch(partText, d),
            }));
            matches.sort((a, b) => b.rating - a.rating);
            return { bestMatch: matches[0], allMatches: matches };
        }

        // ─────────────────────────────────────────────────────────────────────
        // Build a per‑row warning string (hidden; sent only in payload)
        // ─────────────────────────────────────────────────────────────────────
        function getRowWarning(row) {
            const warns = [];

            // Non‑OCR warnings
            if (row._needsReview)            warns.push('Verify whether a ChildPart or BO');
            if (row._similarityScore < 0.95) warns.push('Verify whether the PartNumber/BO name and other fields are correct');

            // OCR confidences   – flag 0 < conf < 0.95
            ['Quantity','Description','Material'].forEach(col => {
                const conf = row[col]?.confidence ?? 0;
                if (conf > 0 && conf < 0.95) warns.push(`Caution in ${col} value`);
            });

            return warns.join('; ');
        }

        // ─────────────────────────────────────────────────────────────────────
        // Initialize Handsontable with 3 rows + 2 empty rows
        // ─────────────────────────────────────────────────────────────────────
        function initializeHandsontable() {
            // On first load, we want 5 rows of empty objects, each with just the 4 columns:
            // “Select Drawing Number” (key “Matched Childpart”), “Quantity”, “Description”, “Material”.
            spreadsheetData = [];
            for (let i = 0; i < 5; i++) {
                spreadsheetData.push({
                    "PartNumber": { text: "", confidence: 0 }, // Hidden column for matching
                    "Type": "",
                    "Matched Childpart": "",
                    Quantity: { text: "", confidence: 0 },
                    Description: { text: "", confidence: 0 },
                    Material: { text: "", confidence: 0 },
                });
            }

            // Only the 4 columns initially: mapping + 3 OCR
            columnsList = [
                "PartNumber", // Hidden from display but needed for matching
                "Type",
                "Matched Childpart",
                "Quantity",
                "Description",
                "Material",
            ];

            renderSpreadsheet();
        }

        // ─────────────────────────────────────────────────────────────────────
        // renderSpreadsheet (combines OCR columns + mapping columns in one view)
        // ─────────────────────────────────────────────────────────────────────
        function renderSpreadsheet() {
            // Prepare column definitions for Handsontable
            const drawingOptions = windowChildParts.slice(); // from fetched backend
            console.log("🔍 renderSpreadsheet: drawingOptions =", drawingOptions);

            // CRITICAL: Filter out PartNumber from visible columns
            const visibleColumns = columnsList.filter(key => key !== "PartNumber");
            console.log("📋 Visible columns:", visibleColumns);

            // Build column definitions only for visible columns
            const columns = visibleColumns.map((key) => {
                const title = COLUMN_TITLES[key] || key;
                const isMatched = key === "Matched Childpart";
                const isType = key === "Type";
                const isOCRcol = ["Quantity", "Description", "Material"].includes(key);

                return {
                    data: isMatched || isType ? key : `${key}.text`,
                    title,
                    type: isMatched || isType ? "dropdown" : "text",
                    editor: isMatched
                        ? "autocomplete"
                        : isType
                            ? "dropdown"
                            : "text",
                    source: isMatched
                        ? ["", ...drawingOptions]
                        : isType
                            ? ["Child Part", "BO"]
                            : undefined,

                    strict: false,
                    allowInvalid: true,
                    readOnly: false, // all columns remain editable
                    wordWrap: true, // ✅ enable per-column wrap

                    renderer: function (hotInstance, td, row, col, prop, value, cellProps) {
                        if (isMatched || isType) {
                            // dropdown renderer for mapping columns
                            Handsontable.renderers.DropdownRenderer.apply(this, arguments);

                            // ✅ ADD: Check for warning needed
                            if (prop === "Type" && value === "BO") {
                                const rowData = hotInstance.getSourceDataAtRow(row);
                                if (rowData["_needsReview"]) {
                                    td.classList.add("needs-review-cell");
                                    td.setAttribute("data-part-number", rowData["PartNumber"]?.text || "");
                                }
                            }

                            if (isMatched && value && value.toString().trim() !== "") {
                                // low‐similarity warning on mapping in real time
                                const rowData = hotInstance.getSourceDataAtRow(row);
                                const partCell = rowData["PartNumber"];
                                const partText = partCell?.text || "";

                                if (partText) {
                                    const sim = sequentialCharacterMatch(partText, value.toString());
                                    if (sim < 0.95) {
                                        td.classList.add("low-similarity-cell");
                                    } else {
                                        td.classList.remove("low-similarity-cell");
                                    }
                                }
                            }
                        } else if (isOCRcol) {
                            // OCR columns: color by confidence
                            Handsontable.renderers.TextRenderer.apply(this, arguments);

                            // ✅ CHECK: Was this cell edited by user?
                            const cellMeta = hotInstance.getCellMeta(row, col);
                            const wasEdited = cellMeta.className && cellMeta.className.includes('user-edited-ocr');

                            if (wasEdited) {
                                // ✅ USER EDITED: Keep it default cell color
                                td.style.backgroundColor = "#0a0a0a";
                            } else {
                                // ✅ OCR DATA: Show confidence colors   
                                const rowData = hotInstance.getSourceDataAtRow(row);
                                const cellObj = rowData[key];  // the { text, confidence } you stored

                                if (cellObj && typeof cellObj === "object" && cellObj.confidence !== undefined) {
                                    const conf = parseFloat(cellObj.confidence || 0);
                                    // Only apply a background if confidence > 0;
                                    // otherwise leave it blank (white).
                                    if (conf > 0) {
                                        if (conf >= 0.95) {
                                            td.style.backgroundColor = "#214028";
                                        } else if (conf >= 0.8) {
                                            td.style.backgroundColor = "#6B3D1C";
                                        } else {
                                            td.style.backgroundColor = "#412628";
                                        }
                                    } else {
                                        // No coloring when confidence is zero (empty cell)
                                        td.style.backgroundColor = "";
                                    }
                                }
                            }
                        }
                    },
                };
            });

            // Destroy any existing Handsontable instance
            const container = document.getElementById("hot");
            if (hot) {
                hot.destroy();
            }

            // Re‐create with our new columns + data
            hot = new Handsontable(container, {
                data: spreadsheetData,
                columns,
                colHeaders: visibleColumns.map((k) => COLUMN_TITLES[k]),
                rowHeaders: true,
                minSpareRows: 1,
                formulas: { engine: HyperFormula, sheetName: 'Sheet1' },
                contextMenu: true,
                dropdownMenu: false,
                filters: true,
                width: '100%',
                heigth: '100%',
                autoColumnSize: true,
                stretchH: 'all',
                wordWrap: true,
                manualColumnResize: true,
                autoRowSize: true,
                outsideClickDeselects: true,
                licenseKey: "non-commercial-and-evaluation",

                // --- NEW afterGetColHeader for OCR upload header area ---
                afterGetColHeader: function (col, TH) {
                    const columnName = visibleColumns[col];
                    console.log(`🔍 Column ${col}: "${columnName}"`);

                    // ← ADD: Label mapping for display
                    const labelMap = {
                        "Quantity": "Quantity",
                        "Description": "Description",
                        "Material": "Material",
                        "Matched Childpart": "Part Number"  // ← This maps to display name
                    };

                    const ocrMap = {
                        "Quantity": "Quantity",
                        "Description": "Description",
                        "Material": "Material",
                        "Matched Childpart": "Part Number"
                    };

                    const ocrKey = ocrMap[columnName];
                    console.log(`🗝️ ocrKey for "${columnName}": "${ocrKey}"`);

                    if (!ocrKey) {
                        console.log(`⏭️ No ocrKey, skipping "${columnName}"`);
                        return;
                    }

                    // Avoid double-mounting
                    if (TH.querySelector(".ocr-upload-area-header")) return;

                    // ← GET: Display label safely
                    const displayLabel = labelMap[columnName] || columnName;

                    // Create new upload area directly (don't move existing ones)
                    const uploadArea = document.createElement("div");
                    uploadArea.className = "ocr-upload-area ocr-upload-area-header";
                    uploadArea.setAttribute("data-column", ocrKey);
                    console.log(`✅ Set data-column to: "${ocrKey}"`);

                    uploadArea.innerHTML = `
                        <span class="upload-icon"><i data-lucide="upload"></i></span>
                        <span class="upload-label">${displayLabel}</span>
                        <button class="upload-clear-btn" onclick="clearUpload(this, event)">×</button>
                        <input type="file" accept="image/*" />
                        <div class="file-status">Processing...</div>
                        <div class="ocr-image-preview" style="display: none !important;"></div>
                    `;

                    // Clear existing TH content and add upload area
                    TH.innerHTML = "";
                    TH.appendChild(uploadArea);

                    // Reinitialize Lucide icons for this new element
                    lucide.createIcons();

                    // Add this single line at the end of your afterGetColHeader function
                    addDragDropListeners(uploadArea);

                    // Reattach event listeners for this specific upload area
                    const input = uploadArea.querySelector("input");
                    const status = uploadArea.querySelector(".file-status");
                    const preview = uploadArea.querySelector(".ocr-image-preview");

                    input.addEventListener("change", () => {
                        const file = input.files[0];
                        if (!file) return;

                        fileStates[ocrKey] = file;
                        status.style.display = "inline-block";
                        const reader = new FileReader();
                        reader.onload = (e) => {
                            preview.innerHTML = `<img src="${e.target.result}" alt="Preview"/>`;
                            uploadArea.classList.add("has-file");
                        };
                        reader.readAsDataURL(file);

                        document.getElementById("ocr-process-btn").disabled = Object.keys(fileStates).length === 0;
                        document.getElementById("ocr-process-btn").click();
                    });
                },

                afterSelectionEnd: function (r, c, r2, c2) {
                    setTimeout(() => {
                        document
                            .querySelectorAll('.wtBorder.current[style*="display: block"]')
                            .forEach((border) => {
                                const style = border.getAttribute("style");
                                if (style.includes("width: 4px")) {
                                    border.setAttribute("style", style.replace("width: 4px", "width: 1px"));
                                }
                                if (style.includes("height: 4px")) {
                                    border.setAttribute("style", style.replace("height: 4px", "height: 1px"));
                                }
                            });
                    }, 0);
                },
            });

            // --- Unified afterChange handler: edit, cut, paste -----------------------------------------------
            hot.addHook('afterChange', (changes, source) => {
                if (!changes) return;

                // ===== 0. COPY: clear any previous cut‑backup so future paste is treated as edit =====
                if (source === 'CopyPaste.copy') {
                    _cutBackup = [];         // Do not capture confidence on copy
                    return;
                }

                // ===== 1. CUT: capture confidences before they disappear =====
                if (source === 'CopyPaste.cut') {

                    _cutBackup = changes.map(([row, prop]) => {
                        const colKey = prop.split('.')[0];
                        const confVal = spreadsheetData[row]?.[colKey]?.confidence ?? 0;
                        return { row, prop, colKey, conf: confVal };
                    });
                    console.log('[CopyPaste.cut] backed‑up confs:', _cutBackup);

                    // wipe confidence from the source cells so color disappears
                    changes.forEach(([row, prop]) => {
                        const colKey = prop.split('.')[0];
                        if (['Quantity', 'Description', 'Material'].includes(colKey)) {
                            spreadsheetData[row][colKey].confidence = 0;
                            const colIndex = hot.propToCol(prop);
                            hot.setCellMeta(row, colIndex, 'className', 'edited-cell user-edited-ocr');
                        }
                    });
                    hot.render();
                    return;
                }

                // ===== 2. PASTE: restore confidences to new cells ===========
                if (source === 'CopyPaste.paste') {
                    console.log('[CopyPaste.paste] applying backup:', _cutBackup);
                    const isCutPaste = _cutBackup.length === changes.length;
                    changes.forEach(([row, prop], idx) => {
                        const colKey = prop.split('.')[0];
                        if (!['Quantity', 'Description', 'Material'].includes(colKey)) return;

                        const colIndex = hot.propToCol(prop);
                        const restored = isCutPaste ? _cutBackup[idx]?.conf ?? 0 : 0;   // 0 for copy‑paste

                        // set confidence
                        spreadsheetData[row][colKey].confidence = restored;

                        // build classes
                        let classes = (hot.getCellMeta(row, colIndex).className || '')
                            .split(' ')
                            .filter(cls => cls !== 'user-edited-ocr' && cls !== 'edited-cell');

                        if (restored === 0) classes.push('edited-cell', 'user-edited-ocr');
                        hot.setCellMeta(row, colIndex, 'className', classes.join(' ').trim());
                    });
                    // clear backup after every paste
                    _cutBackup = [];
                    hot.render();
                    return;
                }

                // ===== 3. STANDARD EDIT branch =================================
                if (source === 'edit') {
                    changes.forEach(([row, prop, oldVal, newVal]) => {
                        if (oldVal === newVal) return;
                        const colIndex = hot.propToCol(prop);

                        // generic edited marker
                        hot.setCellMeta(row, colIndex, 'className', 'edited-cell');

                        // OCR columns: zero confidence & force default bg
                        if (['Quantity.text', 'Description.text', 'Material.text'].includes(prop)) {
                            spreadsheetData[row][prop.split('.')[0]].confidence = 0;
                            hot.setCellMeta(row, colIndex, 'className', 'edited-cell user-edited-ocr');
                            console.log(`🔧 User edited OCR cell: Row ${row}, Column ${prop}`);
                        }

                        // Childpart validation against Type
                        if (prop === 'Matched Childpart') {
                            const rowData = hot.getSourceDataAtRow(row);
                            const typeVal = rowData['Type'];
                            console.log(`🔍 Select Childpart changed: "${newVal}", Type: "${typeVal}"`);
                            if (typeVal === 'Child Part' && newVal && newVal.toString().trim() !== '') {
                                const isValid = windowChildParts.includes(newVal.toString());
                                if (!isValid) {
                                    console.warn(`⚠️ Invalid childpart selection: "${newVal}" - clearing cell`);
                                    hot.setDataAtCell(row, colIndex, '', 'validation-clear');
                                    alert(`"${newVal}" is not a valid child part. Please select from the dropdown list.`);
                                    return;
                                }
                            }
                            // BO type always allowed
                        }

                        // Optional logging for Type edits
                        if (prop === 'Type') {
                            console.log(`🔄 Type changed to: "${newVal}" for row ${row}`);
                        }
                    });
                    hot.render();
                }
            });



        }

        // ─────────────────────────────────────────────────────────────────────
        // addColumn: used by OCR processing to inject a new column's OCR data
        // ─────────────────────────────────────────────────────────────────────
        function addColumn(newColumnData, label) {
            console.log(`🔧 addColumn called with label: "${label}"`);
            console.log(`📊 Data received:`, newColumnData);

            // Now update spreadsheetData for this column without reordering others
            for (let i = 0; i < newColumnData.length; i++) {
                const text = newColumnData[i]?.text || "";
                const confidence = newColumnData[i]?.confidence || 0;

                // Ensure row exists
                if (!spreadsheetData[i]) {
                    spreadsheetData[i] = {};
                }

                // Store OCR data
                spreadsheetData[i][label] = { text, confidence };
                console.log(`📝 Row ${i}: Set ${label} = "${text}" (confidence: ${confidence})`);

                // CRITICAL: PartNumber matching logic
                if (label === "PartNumber" && text.trim() !== "") {
                    console.log(`🔍 Processing PartNumber matching for row ${i}: "${text}"`);
                    console.log(`🎯 Available drawings:`, windowChildParts);

                    if (windowChildParts && windowChildParts.length > 0) {
                        const best = findBestSequentialMatch(text, windowChildParts);
                        console.log(`🎖️ Best match result:`, best);

                        const matchText = best.bestMatch.rating > 0.85 ? best.bestMatch.target : "";
                        console.log(`✨ Match selected (rating ${best.bestMatch.rating}): "${matchText}"`);

                        // Only auto-populate if not manually set
                        const currentMatch = spreadsheetData[i]["Matched Childpart"];
                        if (!currentMatch || currentMatch === "") {
                            if (matchText) {
                                // ✅ GOOD MATCH: Child Part
                                spreadsheetData[i]["Matched Childpart"] = matchText;
                                spreadsheetData[i]["Type"] = "Child Part";
                                console.log(`✅ Auto-populated Matched Childpart: "${matchText}"`);
                            } else {
                                // ❌ NO MATCH: Potential BO with warning
                                spreadsheetData[i]["Matched Childpart"] = text; // Use original PartNumber text
                                spreadsheetData[i]["Type"] = "BO";
                                spreadsheetData[i]["_needsReview"] = true; // Flag for warning icon
                                console.log(`⚠️ No match found - auto-set as BO with warning: "${text}"`);
                            }
                        } else {
                            console.log(`⏭️ Skipped auto-population - already set to: "${currentMatch}"`);
                        }

                        // Store similarity score for reference
                        spreadsheetData[i]["_similarityScore"] = best.bestMatch.rating;

                        // // Auto-populate Type
                        // const currentType = spreadsheetData[i]["Type"];
                        // if (!currentType || currentType === "") {
                        //     // const autoType = matchText ? "Child Part" : "BO";
                        //     const autoType = "Child Part";
                        //     spreadsheetData[i]["Type"] = autoType;
                        //     console.log(`✅ Auto-populated Type: "${autoType}"`);
                        // }
                    } else {
                        console.warn("⚠️ No drawing numbers available for matching");
                    }
                }
            }

            renderSpreadsheet();
        }

        // ─────────────────────────────────────────────────────────────────────
        // OCR Uploads: Multiple zones, event delegation, state per column
        // ─────────────────────────────────────────────────────────────────────
        const uploads = document.querySelectorAll(".ocr-upload-area");
        const fileStates = {};

        uploads.forEach(area => {
            const input = area.querySelector("input");
            const status = area.querySelector(".file-status");
            const preview = area.querySelector(".ocr-image-preview");
            const column = area.dataset.column;

            input.addEventListener("change", () => {
                const file = input.files[0];
                if (!file) return;

                fileStates[column] = file;
                status.style.display = "inline-block";
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.innerHTML = `<img src="${e.target.result}" alt="Preview"/>`;
                    area.classList.add("has-file");
                };
                reader.readAsDataURL(file);

                document.getElementById("ocr-process-btn").disabled = Object.keys(fileStates).length === 0;
                document.getElementById("ocr-process-btn").click();
            });


        });

        // Add this JavaScript code after your existing OCR upload event listeners
        // (Around line 800-850 in your script section)

        // Function to add drag and drop listeners to upload areas
        function addDragDropListeners(uploadArea) {
            // Prevent default drag behaviors on these events
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, preventDefaults, false);
            });

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }

            // Highlight drop area when item is dragged over it
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, highlight, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, unhighlight, false);
            });

            function highlight(e) {
                uploadArea.classList.add('drag-over');
            }

            function unhighlight(e) {
                uploadArea.classList.remove('drag-over');
            }

            // Handle dropped files
            uploadArea.addEventListener('drop', handleDrop, false);

            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;

                if (files.length > 0) {
                    const input = uploadArea.querySelector('input[type="file"]');
                    input.files = files;

                    // Trigger the change event to process the file
                    const event = new Event('change', { bubbles: true });
                    input.dispatchEvent(event);
                }
            }
        }

        // Apply drag & drop listeners to existing upload areas
        document.addEventListener('DOMContentLoaded', function () {
            const uploads = document.querySelectorAll(".ocr-upload-area");
            uploads.forEach(area => {
                addDragDropListeners(area);
            });
        });


        function clearUpload(buttonEl, event) {
            if (event) event.stopPropagation();

            const area = buttonEl.closest(".ocr-upload-area");
            const input = area.querySelector("input");
            const preview = area.querySelector(".ocr-image-preview");
            const status = area.querySelector(".file-status");
            const column = area.dataset.column;

            if (input) input.value = "";
            if (preview) preview.innerHTML = "";
            if (status) status.style.display = "none";

            area.classList.remove("has-file");
            delete fileStates[column];

            document.getElementById("ocr-process-btn").disabled = Object.keys(fileStates).length === 0;
        }

        // ─────────────────────────────────────────────────────────────────────
        // CRITICAL: OCR Processing with correct column mapping
        // ─────────────────────────────────────────────────────────────────────
        document.getElementById("ocr-process-btn").addEventListener("click", async () => {
            const processBtn = document.getElementById("ocr-process-btn");
            const originalText = processBtn.textContent;
            processBtn.disabled = true;
            processBtn.textContent = "Processing...";

            console.log("🚀 Starting OCR processing...");
            console.log("📁 Files to process:", Object.keys(fileStates));

            // Map upload labels to internal column names
            const columnKeyMap = {
                "Part Number": "PartNumber", // Maps to hidden PartNumber column
                "Quantity": "Quantity",
                "Description": "Description",
                "Material": "Material",
            };

            for (const label in fileStates) {
                const internalColumn = columnKeyMap[label];

                // Add this safety check:
                if (!internalColumn) {
                    console.warn(`⚠️ No mapping found for upload label: ${label}`);
                    continue;
                }

                console.log(`🔄 Processing ${label} → ${internalColumn}`);

                const formData = new FormData();
                formData.append("image", fileStates[label]);
                formData.append("mode", "table");
                formData.append("column", internalColumn);

                try {
                    const resp = await fetch("https://ocr-table-extractor.onrender.com", {
                        method: "POST",
                        body: formData,
                    });
                    const data = await resp.json();

                    console.log(`✅ OCR response for ${label}:`, data);

                    if (data.table && Array.isArray(data.table)) {
                        addColumn(data.table, internalColumn);
                    } else {
                        console.warn(`⚠️ No table data in response for ${label}`);
                    }
                } catch (err) {
                    console.error(`❌ OCR error for ${label}:`, err);
                }
            }

            // Clear preview and fileStates after processing
            uploads.forEach(area => {
                area.querySelector(".file-status").style.display = "none";
                area.querySelector(".ocr-image-preview").innerHTML = "";
                area.querySelector("input").value = "";
                area.classList.remove("has-file");
            });

            Object.keys(fileStates).forEach(k => delete fileStates[k]);
            processBtn.disabled = true;
            processBtn.textContent = originalText; // Restore original text

            // Auto-close OCR panel
            const panel = document.getElementById("ocr-panel");
            panel.classList.remove("open");

            console.log("🏁 OCR processing completed");
        });

        // ─────────────────────────────────────────────────────────────────────
        // OCR Panel Toggle: Extract button opens, Close (X) closes
        // ─────────────────────────────────────────────────────────────────────
        document.getElementById("extract-btn").addEventListener("click", () => {
            const panel = document.getElementById("ocr-panel");
            panel.classList.add("open");
        });
        document.getElementById("ocr-close-btn").addEventListener("click", () => {
            const panel = document.getElementById("ocr-panel");
            panel.classList.remove("open");
        });

        // ─────────────────────────────────────────────────────────────────────
        // Show/Hide help popover
        // ─────────────────────────────────────────────────────────────────────
        document.getElementById("help-icon").addEventListener("click", () => {
            const pop = document.getElementById("help-popover");
            pop.style.display = pop.style.display === "none" ? "block" : "none";
        });
        document.addEventListener("click", (e) => {
            if (!e.target.closest("#help-icon")) {
                document.getElementById("help-popover").style.display = "none";
            }
        });

        // ─────────────────────────────────────────────────────────────────────
        // “Submit” button simply calls your existing sendDataToBackend()
        // ─────────────────────────────────────────────────────────────────────
        document.getElementById("submit-btn").addEventListener("click", () => {
            sendDataToBackend();
        });


        // Add this after your table initialization
        document.addEventListener('click', function (e) {
            if (e.target.matches('.needs-review-cell::after') ||
                e.target.closest('.needs-review-cell')) {

                const cell = e.target.closest('.needs-review-cell');
                const partNumber = cell.getAttribute('data-part-number');

                showWarningPopup(e.pageX, e.pageY, partNumber);
            }
        });

        function showWarningPopup(x, y, partNumber) {
            // Remove existing popup
            const existingPopup = document.querySelector('.warning-popup');
            if (existingPopup) existingPopup.remove();

            // Create new popup
            const popup = document.createElement('div');
            popup.className = 'warning-popup';
            popup.style.left = x + 'px';
            popup.style.top = y + 'px';
            popup.style.display = 'block';

            popup.innerHTML = `
        <h4>⚠️ Review Required</h4>
        <p><strong>Part Number:</strong> ${partNumber}</p>
        <p>No Childpart found</p>
        <p>Please verify if this is:</p>
        <p>• A bought-out, OR<br>• A missing child part drawing case</p>
        <button onclick="reportMissingDrawing('${partNumber}')">Coming Soon! - Report Missing Drawing</button>
        <button onclick="closeWarningPopup()">Close</button>
    `;

            document.body.appendChild(popup);

            // Auto-close after 10 seconds
            setTimeout(() => {
                if (popup.parentNode) popup.remove();
            }, 10000);
        }

        function closeWarningPopup() {
            const popup = document.querySelector('.warning-popup');
            if (popup) popup.remove();
        }

        function reportMissingDrawing(partNumber) {
            // TODO: Implement notification/reporting logic
            console.log(`📧 Reporting missing drawing for: ${partNumber}`);
            alert(`Missing drawing reported for: ${partNumber}`);
            closeWarningPopup();
        }




        // ─────────────────────────────────────────────────────────────────────
        // validateRequiredFields (unchanged)
        // ─────────────────────────────────────────────────────────────────────
        // UPDATED: Validation function (doesn't check PartNumber since it's hidden)
        function validateRequiredFields() {
            const missingFields = [];
            let hasValidRow = false;

            spreadsheetData.forEach((row, index) => {
                // Check if row has any meaningful data (Type or Quantity)
                const type = row.Type?.trim();
                const qty = row.Quantity?.text?.trim();

                // Skip completely empty rows
                if (!type && !qty) return;

                hasValidRow = true;

                // Validate required fields for non-empty rows
                if (!qty) missingFields.push(`Row ${index + 1}: Quantity`);
                if (!type) missingFields.push(`Row ${index + 1}: Type`);

                // If Type is "Child Part", require Select Drawing Number
                if ((type === "Child Part" || type === "BO") && !row["Matched Childpart"]?.trim()) {
                    missingFields.push(`Row ${index + 1}: Child Part/BO (required)`);
                }
            });

            return {
                isValid: hasValidRow && missingFields.length === 0,
                missingFields
            };
        }

        function clearTableToDefault() {
            hot.clear(); // ✅ Built-in method that safely clears all data
            hot.deselectCell(); // Remove selection highlighting
            console.log("✅ Table cleared to default state");
        }

        // ─────────────────────────────────────────────────────────────────────
        // Existing sendDataToBackend() function (unchanged from your original)
        // ─────────────────────────────────────────────────────────────────────
        window.childPartsData = [];
        window.boData        = [];

        async function sendDataToBackend() {
            const addDataBtn = document.getElementById("submit-btn");
            const originalText = addDataBtn.textContent;

            try {
                // Provide some visual feedback (you can customize as needed)
                addDataBtn.disabled = true;
                addDataBtn.textContent = "Sending...";
                // Validate required fields:
                const validation = validateRequiredFields();
                if (!validation.isValid) {
                    alert(
                        `Missing Required Fields:\n${validation.missingFields.join(
                            ", "
                        )}\nRequired fields:\n- Child Part/BO, Quantity, Type`
                    );
                    addDataBtn.textContent = originalText;
                    return;
                }

                const urlParams = new URLSearchParams(window.location.search);
                const project = urlParams.get("project");
                const parentDrawingNumber = urlParams.get("parentdrgnum");
                const partNumber = urlParams.get("part");
                if (!project || !parentDrawingNumber || !partNumber) {
                    throw new Error("Missing required URL params");
                }

                // Build ChildParts & BO arrays **in the visual row order**
                // const childPartsData = [];
                // const boData = [];
                childPartsData.length = 0;  // reset
                boData.length = 0;

                for (let vRow = 0; vRow < hot.countRows(); vRow++) {
                    const pRow = hot.toPhysicalRow(vRow);   // map visual → physical
                    if (pRow == null) continue;             // skip spare / trimmed rows

                    const row = spreadsheetData[pRow];
                    const qty = row.Quantity?.text?.trim();
                    const type = row.Type?.trim();

                    // Skip completely empty or incomplete rows
                    if (!qty && !type) continue;
                    if (!qty || !type) continue;

                    if (type === "Child Part") {
                        childPartsData.push({
                            quantity: qty,
                            description: row.Description?.text?.trim() || "",
                            material: row.Material?.text?.trim() || "",
                            drawingNumber: row["Matched Childpart"] || "",
                            ocrWarning: getRowWarning(row)
                        });
                    } else if (type === "BO") {
                        boData.push({
                            quantity: qty,
                            description: row.Description?.text?.trim() || "",
                            material: row.Material?.text?.trim() || "",
                            boughtoutPartNumber: row["Matched Childpart"] || "",
                            ocrWarning: getRowWarning(row)
                        });
                    }
                }

                // Send to backend
                let successful = 0,
                    total = 0;

                if (childPartsData.length) {
                    total++;
                    const respChild = await fetch(
                        "https://ocr-table-extractor.onrender.com/add-child-parts",
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                rows: childPartsData,
                                project,
                                parentDrawingNumber,
                                partNumber,
                            }),
                        }
                    );
                    if (!respChild.ok) {
                        throw new Error(`Failed to add Child Parts: ${await respChild.text()}`);
                    }
                    successful++;
                }
                if (boData.length) {
                    total++;
                    const respBo = await fetch(
                        "https://ocr-table-extractor.onrender.com/add-bo-parts",
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                rows: boData,
                                project,
                                parentDrawingNumber,
                                partNumber,
                            }),
                        }
                    );
                    if (!respBo.ok) {
                        throw new Error(`Failed to add BO Parts: ${await respBo.text()}`);
                    }
                    successful++;
                }

                if (successful === total && total > 0) {
                    alert(
                        `Data added successfully!\n- Child Parts: ${childPartsData.length}\n- BO Parts: ${boData.length}`
                    );
                    clearTableToDefault();
                } else {
                    throw new Error("No data was processed");
                }
            } catch (error) {
                console.error("❌ Error sending data:", error);
                alert(`Error adding data: ${error.message}`);
            } finally {
                addDataBtn.disabled = false;
                addDataBtn.textContent = "Submit";
            }
        }

        // --- Ensure OCR upload header areas use correct data-column attributes (internal keys) ---
        // This runs once on DOMContentLoaded to fix any "data-column" attributes for header upload areas
        document.addEventListener("DOMContentLoaded", function () {
            // Map display titles to internal keys
            const columnKeyMap = {
                "Part Number": "PartNumber",
                "Quantity": "Quantity",
                "Description": "Description",
                "Material": "Material",
            };
            // Find all .ocr-upload-area in the header-row and update data-column
            document.querySelectorAll(".header-row .ocr-upload-area").forEach(area => {
                const oldCol = area.getAttribute("data-column");
                if (columnKeyMap[oldCol]) {
                    area.setAttribute("data-column", columnKeyMap[oldCol]);
                }
            });
            // Add a marker class for header upload areas (so afterGetColHeader can find them)
            document.querySelectorAll(".header-row .ocr-upload-area").forEach(area => {
                area.classList.add("ocr-upload-area-header");
            });
        });
        lucide.createIcons();

    </script>

</body>

</html>
