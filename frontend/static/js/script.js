// Элементы DOM
const dropArea = document.getElementById('dropArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const fileInfo = document.getElementById('fileInfo');
const processBtn = document.getElementById('processBtn');
const logOutput = document.getElementById('logOutput');
const clearLogBtn = document.getElementById('clearLogBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusIndicator = document.querySelector('.status-indicator');

let source;  // Для хранения EventSource
let currentFile = null;
let resultFilename = null; // Для хранения имени результирующего файла

// Обработчики drag-and-drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, () => {
    dropArea.classList.add('active');
  }, false);
});

['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, () => {
    dropArea.classList.remove('active');
  }, false);
});

dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
  const dt = e.dataTransfer;
  const file = dt.files[0];
  handleFile(file);
}

// Выбор файла через кнопку
browseBtn.addEventListener('click', () => {
  fileInput.click();
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) {
    handleFile(fileInput.files[0]);
  }
});

// Обработка выбранного файла
function handleFile(file) {
  if (file && file.name.endsWith('.zip')) {
    currentFile = file;
    fileInfo.textContent = `Выбран файл: ${file.name} (${formatBytes(file.size)})`;
    processBtn.disabled = false;

    // Сброс состояния скачивания при новом выборе файла
    downloadBtn.disabled = true;
    downloadBtn.classList.remove('active');
    resultFilename = null;
  } else {
    fileInfo.textContent = 'Ошибка: выбранный файл не является ZIP-архивом';
    processBtn.disabled = true;
  }
}

// Форматирование размера файла
function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Очистка логов
clearLogBtn.addEventListener('click', () => {
  logOutput.textContent = '';
});

// Скачивание результата
downloadBtn.addEventListener('click', () => {
  if (resultFilename) {
    // Кодируем имя файла для безопасной передачи в URL
    const encodedFilename = encodeURIComponent(resultFilename);
    window.location.href = `/download/${encodedFilename}`;
  }
});

// Запуск обработки
processBtn.addEventListener('click', async () => {
  if (!currentFile) return;

  // Сброс состояния перед запуском
  processBtn.disabled = true;
  statusIndicator.classList.add('active');
  downloadBtn.disabled = true;
  downloadBtn.classList.remove('active');
  logOutput.textContent = '';
  resultFilename = null;

  // Закрываем предыдущее соединение SSE
  if (source) {
    source.close();
  }

  // Открываем новое соединение SSE для получения логов
  source = new EventSource('/logs');

  source.onmessage = (event) => {
    logOutput.textContent += event.data + '\n';
    // Автопрокрутка
    logOutput.scrollTop = logOutput.scrollHeight;

    // Проверка завершения обработки
    if (event.data.includes('Обработка завершена')) {
      // Активируем кнопку скачивания
      downloadBtn.disabled = false;
      downloadBtn.classList.add('active');

      // Закрываем соединение SSE
      source.close();
      processBtn.disabled = false;
      statusIndicator.classList.remove('active');
    }
    else if (event.data.includes('Ошибка')) {
      source.close();
      processBtn.disabled = false;
      statusIndicator.classList.remove('active');
    }
  };

  source.onerror = () => {
    logOutput.textContent += 'Ошибка подключения к логам\n';
    processBtn.disabled = false;
    statusIndicator.classList.remove('active');
    source.close();
  };

  // Отправка файла на сервер
  const formData = new FormData();
  formData.append('zip_file', currentFile);

  try {
    const response = await fetch('/process', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    if (result.status === 'success') {
      // Сохраняем имя результирующего файла
      resultFilename = result.result_filename;
    } else {
      logOutput.textContent += `Ошибка сервера: ${result.message}\n`;
      processBtn.disabled = false;
      statusIndicator.classList.remove('active');
      source.close();
    }
  } catch (error) {
    logOutput.textContent += `Ошибка при отправке файла: ${error.message}\n`;
    processBtn.disabled = false;
    statusIndicator.classList.remove('active');
    source.close();
  }
});