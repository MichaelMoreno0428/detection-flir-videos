document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadContent = document.getElementById('uploadContent');
    const previewArea = document.getElementById('previewArea');
    const previewImage = document.getElementById('previewImage');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileType = document.getElementById('fileType');
    const changeImageBtn = document.getElementById('changeImageBtn');
    const controlsSection = document.getElementById('controlsSection');
    const modelSelect = document.getElementById('modelSelect');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue = document.getElementById('thresholdValue');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const resultContainer = document.getElementById('resultContainer');
    const result = document.getElementById('result');
    const exportBtn = document.getElementById('exportBtn');

    // Variables de estado
    let selectedFile = null;
    let isDragging = false;
    let currentDetections = null;
    let currentModel = 'rtdetr';

    // Diccionario de clases mejorado
    const classLabels = {
        rtdetr: {
            0: 'Vehículos',
            1: 'Estructuras', 
            2: 'Carreteras',
            3: 'Ríos',
            4: 'Áreas descubiertas'
        },
        yolo: {
            0: 'Vehículos',
            1: 'Estructuras', 
            2: 'Carreteras',
            3: 'Ríos',
            4: 'Áreas descubiertas'
        }
    };

    // Función para obtener el nombre de la clase
    function getClassName(label, model = currentModel) {
        const numericLabel = parseInt(label);
        const labels = classLabels[model] || classLabels.rtdetr;
        
        if (!isNaN(numericLabel) && labels.hasOwnProperty(numericLabel)) {
            return labels[numericLabel];
        }
        
        // Si es un string que ya es una clase conocida, retornarlo
        if (typeof label === 'string' && Object.values(labels).includes(label)) {
            return label;
        }
        
        return label;
    }

    // Inicialización
    init();

    function init() {
        setupEventListeners();
        updateThresholdDisplay();
        addAnimationDelays();
        // Configurar el modelo inicial
        currentModel = modelSelect.value;
    }

    function setupEventListeners() {
        // Upload events
        uploadArea.addEventListener('click', handleUploadClick);
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        
        // File input
        fileInput.addEventListener('change', handleFileSelect);
        
        // Change image button
        changeImageBtn.addEventListener('click', handleChangeImage);
        
        // Controls
        modelSelect.addEventListener('change', handleModelChange);
        thresholdSlider.addEventListener('input', updateThresholdDisplay);
        analyzeBtn.addEventListener('click', handleAnalyze);
        
        // Export button
        exportBtn.addEventListener('click', handleExport);
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, preventDefaults, false);
        });
        
        // Scroll effects
        window.addEventListener('scroll', handleScroll);
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleUploadClick(e) {
        if (!previewArea.classList.contains('d-none')) return;
        fileInput.click();
    }

    function handleDragOver(e) {
        e.preventDefault();
        if (!isDragging) {
            isDragging = true;
            uploadArea.classList.add('dragover');
        }
    }

    function handleDragLeave(e) {
        e.preventDefault();
        if (!uploadArea.contains(e.relatedTarget)) {
            isDragging = false;
            uploadArea.classList.remove('dragover');
        }
    }

    function handleDrop(e) {
        e.preventDefault();
        isDragging = false;
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (validateFile(file)) {
                selectFile(file);
            }
        }
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file && validateFile(file)) {
            selectFile(file);
        }
    }

    function handleChangeImage() {
        resetToUpload();
    }

    function handleModelChange(e) {
        currentModel = e.target.value;
        // Si hay resultados previos, limpiarlos
        if (currentDetections) {
            hideResults();
        }
        showToast(`Modelo cambiado a ${currentModel.toUpperCase()}`, 'info');
    }

    function validateFile(file) {
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/tif'];
        const maxSize = 50 * 1024 * 1024; // 50MB
        
        if (!validTypes.includes(file.type)) {
            showToast('Formato de archivo no válido. Use JPG, PNG o TIFF.', 'error');
            return false;
        }
        
        if (file.size > maxSize) {
            showToast('El archivo es demasiado grande. Tamaño máximo: 50MB.', 'error');
            return false;
        }
        
        return true;
    }

    function selectFile(file) {
        selectedFile = file;
        showPreview(file);
        showControls();
        enableAnalyzeButton();
        hideResults();
        showToast('Imagen cargada correctamente', 'success');
    }

    function showPreview(file) {
        // Crear URL para la imagen
        const imageUrl = URL.createObjectURL(file);
        
        // Actualizar preview
        previewImage.src = imageUrl;
        previewImage.onload = () => {
            URL.revokeObjectURL(imageUrl);
        };
        
        // Actualizar información del archivo
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileType.textContent = file.type.split('/')[1].toUpperCase();
        
        // Animar transición
        uploadContent.style.opacity = '0';
        uploadContent.style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            uploadContent.classList.add('d-none');
            previewArea.classList.remove('d-none');
            
            // Animar entrada del preview
            previewArea.style.opacity = '0';
            previewArea.style.transform = 'translateY(20px)';
            
            requestAnimationFrame(() => {
                previewArea.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                previewArea.style.opacity = '1';
                previewArea.style.transform = 'translateY(0)';
            });
        }, 200);
        
        // Reset upload area border
        uploadArea.style.border = '2px solid rgba(99, 102, 241, 0.3)';
        uploadArea.style.cursor = 'default';
    }

    function showControls() {
        setTimeout(() => {
            controlsSection.classList.add('visible');
        }, 300);
    }

    function enableAnalyzeButton() {
        analyzeBtn.disabled = false;
        analyzeBtn.style.animation = 'pulse 0.6s ease';
        setTimeout(() => {
            analyzeBtn.style.animation = '';
        }, 600);
    }

    function resetToUpload() {
        selectedFile = null;
        
        // Ocultar preview y mostrar upload
        previewArea.style.opacity = '0';
        previewArea.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            previewArea.classList.add('d-none');
            uploadContent.classList.remove('d-none');
            
            uploadContent.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            uploadContent.style.opacity = '1';
            uploadContent.style.transform = 'scale(1)';
            
            // Reset upload area
            uploadArea.style.border = '2px dashed rgba(148, 163, 184, 0.3)';
            uploadArea.style.cursor = 'pointer';
        }, 200);
        
        // Ocultar controles y resultados
        controlsSection.classList.remove('visible');
        hideResults();
        
        // Deshabilitar botón
        analyzeBtn.disabled = true;
        
        // Limpiar input
        fileInput.value = '';
    }

    function updateThresholdDisplay() {
        const value = parseFloat(thresholdSlider.value);
        thresholdValue.textContent = value.toFixed(2);
        
        // Actualizar color del valor según el threshold
        if (value >= 0.8) {
            thresholdValue.style.color = '#10b981'; // success
        } else if (value >= 0.5) {
            thresholdValue.style.color = '#f59e0b'; // warning  
        } else {
            thresholdValue.style.color = '#ef4444'; // danger
        }
    }

    async function handleAnalyze() {
        if (!selectedFile) {
            showToast('Por favor, selecciona una imagen antes de analizar.', 'error');
            return;
        }

        try {
            // Mostrar loading
            showLoading();
            setAnalyzeButtonLoading(true);
            hideResults();

            // Preparar datos
            const formData1 = new FormData();
            const formData2 = new FormData();
            formData1.append('file', selectedFile);
            formData2.append('file', selectedFile);
            
            // Añadir threshold
            const threshold = thresholdSlider.value;
            if (currentModel === 'rtdetr') {
                formData1.append('threshold', threshold);
                formData2.append('threshold', threshold);
            }

            // Construir URLs basadas en el modelo seleccionado
            const jsonEndpoint = `/predict/${currentModel}`;
            const imageEndpoint = `/predict/${currentModel}/image`;

            // Realizar peticiones en paralelo
            const [jsonResponse, imageResponse] = await Promise.all([
                fetch(jsonEndpoint, {
                    method: 'POST',
                    body: formData1
                }),
                fetch(imageEndpoint, {
                    method: 'POST', 
                    body: formData2
                })
            ]);

            // Verificar respuestas
            if (!jsonResponse.ok) {
                const errorText = await jsonResponse.text();
                throw new Error(`Error en la detección: ${jsonResponse.status} - ${errorText}`);
            }
            
            if (!imageResponse.ok) {
                const errorText = await imageResponse.text();
                throw new Error(`Error en la imagen procesada: ${imageResponse.status} - ${errorText}`);
            }

            // Procesar resultados
            const responseData = await jsonResponse.json();
            const detections = responseData.detections || [];
            const imageBlob = await imageResponse.blob();
            
            // Guardar detecciones para exportar
            currentDetections = {
                model: currentModel,
                detections: detections,
                threshold: parseFloat(threshold),
                timestamp: new Date().toISOString()
            };
            
            // Mostrar resultados
            await displayResults(detections, imageBlob);
            
            showToast(`Análisis completado con ${currentModel.toUpperCase()}. ${detections.length} objeto(s) detectado(s).`, 'success');

        } catch (error) {
            console.error('Error durante el análisis:', error);
            showToast(`Error durante el análisis: ${error.message}`, 'error');
        } finally {
            hideLoading();
            setAnalyzeButtonLoading(false);
        }
    }

    async function displayResults(detections, imageBlob) {
        // Crear URL de la imagen
        const imageUrl = URL.createObjectURL(imageBlob);
        
        // Limpiar resultados anteriores
        result.innerHTML = '';
        
        // Crear contenedor de imagen
        const imageContainer = document.createElement('div');
        imageContainer.className = 'text-center mb-4';
        
        const img = document.createElement('img');
        img.src = imageUrl;
        img.className = 'results-image fade-in-up';
        img.alt = 'Imagen con detecciones';
        
        imageContainer.appendChild(img);
        result.appendChild(imageContainer);
        
        // Esperar a que la imagen cargue
        await new Promise((resolve) => {
            img.onload = resolve;
        });
        
        // Crear resumen
        const summary = createSummary(detections);
        result.appendChild(summary);
        
        // Crear tabla si hay detecciones
        if (detections && detections.length > 0) {
            const table = createResultsTable(detections);
            result.appendChild(table);
        }
        
        // Mostrar sección de resultados
        resultContainer.classList.remove('d-none');
        resultContainer.style.animation = 'fadeInUp 0.6s ease';
        
        // Scroll suave a resultados
        setTimeout(() => {
            resultContainer.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 300);
        
        // Limpiar URL después de un tiempo
        setTimeout(() => URL.revokeObjectURL(imageUrl), 10000);
    }

    function createSummary(detections) {
        const summary = document.createElement('div');
        summary.className = 'alert mb-4';
        
        const count = detections ? detections.length : 0;
        const icon = count > 0 ? 'check-circle-fill' : 'info-circle';
        
        let content = '';
        
        if (count > 0) {
            // Contar objetos por tipo
            const objectCounts = {};
            detections.forEach(detection => {
                const className = getClassName(detection.label || detection.name);
                objectCounts[className] = (objectCounts[className] || 0) + 1;
            });
            
            // Crear lista de objetos detectados
            const objectList = Object.entries(objectCounts)
                .map(([className, count]) => `${count} ${className.toLowerCase()}`)
                .join(', ');
            
            content = `
                <h5 class="mb-2">¡Análisis completado exitosamente!</h5>
                <p class="mb-2">Se detectaron <strong>${count} objeto(s)</strong> en la imagen térmica usando <strong>${currentModel.toUpperCase()}</strong>:</p>
                <div class="detected-objects">
                    <i class="bi bi-eye me-2"></i>
                    <strong>${objectList}</strong>
                </div>
            `;
        } else {
            content = `
                <h5 class="mb-2">Análisis completado</h5>
                <p class="mb-0">No se detectaron objetos con el modelo <strong>${currentModel.toUpperCase()}</strong>. Intenta ajustar el umbral de confianza o verificar que la imagen contenga elementos detectables.</p>
            `;
        }
        
        summary.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="bi bi-${icon} me-3 fs-4" style="margin-top: 2px;"></i>
                <div class="flex-grow-1">
                    ${content}
                </div>
            </div>
        `;
        
        summary.style.background = count > 0 
            ? 'rgba(16, 185, 129, 0.1)'
            : 'rgba(59, 130, 246, 0.1)';
        summary.style.border = `1px solid ${count > 0 ? '#10b981' : '#3b82f6'}`;
        summary.style.borderRadius = 'var(--radius)';
        summary.style.color = '#e2e8f0';
        summary.style.padding = '1rem';
        
        return summary;
    }

    function createResultsTable(detections) {
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-responsive';
        
        const table = document.createElement('table');
        table.className = 'results-table';
        
        // Header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th><i class="bi bi-hash me-2"></i>#</th>
                <th><i class="bi bi-tag me-2"></i>Objeto</th>
                <th><i class="bi bi-percent me-2"></i>Confianza</th>
                <th><i class="bi bi-geo me-2"></i>Posición</th>
                <th><i class="bi bi-speedometer2 me-2"></i>Estado</th>
            </tr>
        `;
        table.appendChild(thead);
        
        // Body
        const tbody = document.createElement('tbody');
        detections.forEach((detection, index) => {
            const row = createDetectionRow(detection, index);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        tableContainer.appendChild(table);
        
        // Animar filas
        setTimeout(() => {
            const rows = tbody.querySelectorAll('tr');
            rows.forEach((row, index) => {
                row.style.opacity = '0';
                row.style.transform = 'translateX(-20px)';
                setTimeout(() => {
                    row.style.transition = 'all 0.3s ease';
                    row.style.opacity = '1';
                    row.style.transform = 'translateX(0)';
                }, index * 100);
            });
        }, 200);
        
        return tableContainer;
    }

    function createDetectionRow(detection, index) {
        const row = document.createElement('tr');
        
        const confidence = (detection.score * 100).toFixed(1);
        const confidenceClass = confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low';
        const coordinates = detection.box.map(coord => Math.round(coord)).join(', ');
        const className = getClassName(detection.label || detection.name);
        const originalLabel = detection.label || detection.name || 'N/A';
        
        row.innerHTML = `
            <td><span class="detection-badge" style="background: rgba(99, 102, 241, 0.2); color: #a5b4fc;">${index + 1}</span></td>
            <td>
                <div>
                    <strong>${className}</strong>
                    ${originalLabel !== className ? `<br><small style="color: #94a3b8; font-size: 0.75rem;">ID: ${originalLabel}</small>` : ''}
                </div>
            </td>
            <td><span class="detection-badge confidence-${confidenceClass}">${confidence}%</span></td>
            <td><code style="font-size: 0.8rem; color: #94a3b8;">[${coordinates}]</code></td>
            <td><span class="detection-badge confidence-${confidenceClass}">
                ${confidence >= 80 ? 'Alta' : confidence >= 60 ? 'Media' : 'Baja'}
            </span></td>
        `;
        
        return row;
    }

    function hideResults() {
        resultContainer.classList.add('d-none');
        currentDetections = null;
    }

    function showLoading() {
        loadingOverlay.classList.remove('d-none');
        document.body.style.overflow = 'hidden';
    }

    function hideLoading() {
        loadingOverlay.classList.add('d-none');
        document.body.style.overflow = '';
    }

    function setAnalyzeButtonLoading(isLoading) {
        if (isLoading) {
            analyzeBtn.classList.add('loading');
            analyzeBtn.disabled = true;
        } else {
            analyzeBtn.classList.remove('loading');
            analyzeBtn.disabled = selectedFile ? false : true;
        }
    }

    function handleExport() {
        if (!currentDetections || !currentDetections.detections) {
            showToast('No hay resultados para exportar.', 'error');
            return;
        }

        const data = {
            timestamp: currentDetections.timestamp,
            model: currentDetections.model,
            image: selectedFile.name,
            imageSize: selectedFile.size,
            threshold: currentDetections.threshold,
            totalDetections: currentDetections.detections.length,
            classLabels: classLabels[currentDetections.model],
            detections: currentDetections.detections.map((detection, index) => ({
                id: index + 1,
                originalLabel: detection.label || detection.name,
                className: getClassName(detection.label || detection.name, currentDetections.model),
                confidence: parseFloat((detection.score * 100).toFixed(2)),
                boundingBox: detection.box.map(coord => Math.round(coord)),
                coordinates: {
                    x1: Math.round(detection.box[0]),
                    y1: Math.round(detection.box[1]),
                    x2: Math.round(detection.box[2]),
                    y2: Math.round(detection.box[3])
                }
            }))
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `flir_analysis_${currentDetections.model}_${new Date().getTime()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showToast('Resultados exportados correctamente.', 'success');
    }

    function showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        
        // Remover toasts existentes después de 3 segundos
        const existingToasts = toastContainer.querySelectorAll('.toast');
        if (existingToasts.length >= 3) {
            existingToasts[0].remove();
        }
        
        // Crear nuevo toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = type === 'error' ? 'exclamation-triangle-fill' :
                     type === 'success' ? 'check-circle-fill' : 'info-circle-fill';
        
        toast.innerHTML = `
            <div class="toast-body">
                <i class="bi bi-${icon} me-3 fs-5"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" onclick="this.closest('.toast').remove()">×</button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove después de 5 segundos
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function addAnimationDelays() {
        // Agregar delays a elementos para animaciones escalonadas
        const cards = document.querySelectorAll('.upload-section, .controls-section, .results-section');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

    function handleScroll() {
        const navbar = document.querySelector('.glass-nav');
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(15, 23, 42, 0.95)';
        } else {
            navbar.style.background = 'rgba(15, 23, 42, 0.8)';
        }
    }

    // Event listener global para botones de cambiar imagen
    document.addEventListener('click', (e) => {
        if (e.target.closest('#changeImageBtn') || e.target.closest('.btn-change')) {
            resetToUpload();
        }
    });

    // Event listener para cerrar toasts
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-close')) {
            e.target.closest('.toast').remove();
        }
    });

    // Agregar estilos adicionales dinámicamente
    const additionalStyles = document.createElement('style');
    additionalStyles.textContent = `
        .detected-objects {
            background: rgba(99, 102, 241, 0.1);
            padding: 0.5rem;
            border-radius: 6px;
            border-left: 3px solid var(--primary);
            margin-top: 0.5rem;
        }
        
        code {
            background: rgba(148, 163, 184, 0.1);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Inconsolata', 'Roboto Mono', monospace;
        }
        
        .table-responsive {
            border-radius: var(--radius);
            overflow: hidden;
        }
        
        .flex-grow-1 {
            flex: 1 1 auto;
        }
        
        .fs-4 {
            font-size: 1.5rem;
        }
        
        .fs-5 {
            font-size: 1.25rem;
        }
        
        .me-3 {
            margin-right: 1rem;
        }
        
        .mb-2 {
            margin-bottom: 0.5rem;
        }
        
        .mb-4 {
            margin-bottom: 1.5rem;
        }
        
        .text-success {
            color: var(--success) !important;
        }
    `;
    document.head.appendChild(additionalStyles);

    console.log('FLIR AI Application initialized successfully');
});