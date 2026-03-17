class FileShareSystem {
    constructor() {
        this.currentPath = '';
        this.selectedFiles = new Set();
        this.uploads = new Map();
        this.eventSource = null;
        this.pendingUploads = 0;
        this.init();
    }

    async init() {
        try {
            // 先检查后端是否可用
            const healthResponse = await fetch('/api/health');
            if (!healthResponse.ok) {
                throw new Error('Backend service unavailable');
            }

            const healthData = await healthResponse.json();
            console.log('Connected to backend, base_dir:', healthData.base_dir);

            await this.loadFiles();
            this.initEventListeners();
            this.initDragAndDrop();
            this.initSSE();

            // 加载存储信息
            this.loadStorageInfo();

            console.log('FileShareSystem initialized successfully');
        } catch (error) {
            console.error('Initialization error:', error);
            const fileList = document.getElementById('fileList');
            if (fileList) {
                fileList.innerHTML = '<div class="error">无法连接到服务器，请确保后端服务已启动</div>';
            }
        }
    }

    initEventListeners() {
        // 按钮事件
        document.getElementById('new-folder-btn')?.addEventListener('click', () => this.showNewFolderModal());
        document.getElementById('upload-btn')?.addEventListener('click', () => this.uploadFiles());
        document.getElementById('upload-folder-btn')?.addEventListener('click', () => this.uploadFolder());
        document.getElementById('refresh-btn')?.addEventListener('click', () => this.loadFiles());
        document.getElementById('change-path-btn')?.addEventListener('click', () => this.showPathModal());
        document.getElementById('delete-selected-btn')?.addEventListener('click', () => this.deleteSelected());

        // 全选复选框
        document.getElementById('select-all')?.addEventListener('change', (e) => {
            this.toggleSelectAll(e.target.checked);
        });

        // 上传队列最小化
        document.getElementById('minimize-queue')?.addEventListener('click', () => {
            const queue = document.getElementById('uploadQueue');
            const icon = document.querySelector('#minimize-queue i');
            if (queue && icon) {
                if (queue.style.display === 'none') {
                    queue.style.display = 'block';
                    icon.className = 'fas fa-minus';
                } else {
                    queue.style.display = 'none';
                    icon.className = 'fas fa-plus';
                }
            }
        });

        // 模态框关闭
        document.querySelectorAll('.close, #cancelPathBtn').forEach(btn => {
            btn?.addEventListener('click', () => {
                document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
            });
        });

        // 新建文件夹
        document.getElementById('createFolderBtn')?.addEventListener('click', () => this.createFolder());

        // 更新路径
        document.getElementById('updatePathBtn')?.addEventListener('click', () => this.updateStoragePath());

        // 浏览路径按钮
        document.getElementById('browsePathBtn')?.addEventListener('click', () => this.browseFolder());

        // 路径输入预览
        document.getElementById('newPath')?.addEventListener('input', (e) => {
            const preview = document.getElementById('pathPreview');
            if (preview) {
                preview.textContent = `预览: ${e.target.value}`;
            }
        });

        // 点击模态框外部关闭
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });

        // 键盘事件
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
            }
        });
    }

    async loadStorageInfo() {
        try {
            const response = await fetch('/api/storage');
            if (response.ok) {
                const info = await response.json();
                this.updateStorageDisplay(info);
            }
        } catch (error) {
            console.error('Error loading storage info:', error);
        }
    }

    initDragAndDrop() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');

            const items = e.dataTransfer.items;
            const uploadPromises = [];

            for (let i = 0; i < items.length; i++) {
                const item = items[i].webkitGetAsEntry();
                if (item) {
                    uploadPromises.push(this.handleDroppedItem(item, this.currentPath));
                }
            }

            // 显示上传队列
            const queue = document.getElementById('uploadQueue');
            if (queue) {
                queue.style.display = 'block';
            }

            // 等待所有上传完成
            await Promise.all(uploadPromises);

            // 所有上传完成后刷新文件列表
            await this.loadFiles();
        });
    }

    initSSE() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        try {
            this.eventSource = new EventSource('/api/storage/stream');

            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.updateStorageDisplay(data);
                } catch (e) {
                    console.error('Error parsing SSE data:', e);
                }
            };

            this.eventSource.onerror = (error) => {
                console.error('SSE connection error:', error);
                this.eventSource.close();
                // 尝试重新连接
                setTimeout(() => {
                    this.initSSE();
                }, 10000);
            };
        } catch (error) {
            console.error('Error initializing SSE:', error);
        }
    }

    async loadFiles(path = this.currentPath) {
        const fileList = document.getElementById('fileList');
        if (!fileList) return;

        fileList.innerHTML = '<div class="loading">加载中...</div>';

        try {
            const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                throw new Error('Failed to load files');
            }
            const data = await response.json();

            this.currentPath = data.current_path;
            this.renderFileList(data.files);
            this.updateBreadcrumb();
            this.clearSelection();
        } catch (error) {
            console.error('Error loading files:', error);
            fileList.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
        }
    }

    renderFileList(files) {
        const fileList = document.getElementById('fileList');
        if (!fileList) return;

        if (files.length === 0) {
            fileList.innerHTML = '<div class="empty-folder">文件夹为空</div>';
            return;
        }

        let html = '';
        files.forEach(file => {
            const icon = file.is_dir ? 'fa-folder' : this.getFileIcon(file.name);
            const size = file.is_dir ? '-' : this.formatFileSize(file.size);
            const modified = new Date(file.modified).toLocaleString();
            const encodedPath = encodeURIComponent(file.path);

            html += `
                <div class="file-item ${file.is_dir ? 'folder-item' : ''}" data-path="${file.path}">
                    <div class="checkbox-col">
                        <input type="checkbox" class="file-checkbox" data-path="${file.path}">
                    </div>
                    <div class="name-col ${file.is_dir ? 'folder' : ''}">
                        <i class="fas ${icon}"></i>
                        <span class="file-name" data-path="${file.path}" data-is-dir="${file.is_dir}">${this.escapeHtml(file.name)}</span>
                    </div>
                    <div class="size-col">${size}</div>
                    <div class="modified-col">${modified}</div>
                    <div class="actions-col">
                        <div class="file-actions">
                            ${!file.is_dir ? `
                                <button class="preview" title="预览" onclick="event.stopPropagation(); window.fileSystem.previewFile('${file.path}')">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="download" title="下载" onclick="event.stopPropagation(); window.fileSystem.downloadFile('${file.path}')">
                                    <i class="fas fa-download"></i>
                                </button>
                            ` : ''}
                            <button class="delete" title="删除" onclick="event.stopPropagation(); window.fileSystem.deleteFiles(['${file.path}'])">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        fileList.innerHTML = html;
        this.attachFileItemEvents();
    }

    attachFileItemEvents() {
        // 文件点击导航
        document.querySelectorAll('.file-name').forEach(el => {
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                const path = e.target.dataset.path;
                const isDir = e.target.dataset.isDir === 'true';

                if (isDir) {
                    this.loadFiles(path);
                }
            });
        });

        // 复选框事件
        document.querySelectorAll('.file-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                e.stopPropagation();
                const path = e.target.dataset.path;
                if (e.target.checked) {
                    this.selectedFiles.add(path);
                } else {
                    this.selectedFiles.delete(path);
                }
                this.updateSelectionUI();
            });
        });

        // 文件项点击（用于选中）
        document.querySelectorAll('.file-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox' && !e.target.closest('.file-actions')) {
                    const checkbox = item.querySelector('.file-checkbox');
                    if (checkbox) {
                        checkbox.checked = !checkbox.checked;
                        const event = new Event('change', { bubbles: true });
                        checkbox.dispatchEvent(event);
                    }
                }
            });
        });
    }

    updateBreadcrumb() {
        const breadcrumb = document.getElementById('breadcrumb');
        if (!breadcrumb) return;

        const paths = this.currentPath.split('/').filter(p => p);

        let html = '<span class="breadcrumb-item" data-path="">根目录</span>';
        let currentPath = '';

        paths.forEach((path) => {
            currentPath += (currentPath ? '/' : '') + path;
            html += `<span class="breadcrumb-item" data-path="${currentPath}">${this.escapeHtml(path)}</span>`;
        });

        breadcrumb.innerHTML = html;

        // 添加面包屑点击事件
        document.querySelectorAll('.breadcrumb-item').forEach(el => {
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                this.loadFiles(e.target.dataset.path);
            });
        });
    }

    updateSelectionUI() {
        const count = this.selectedFiles.size;
        const selectedCountEl = document.getElementById('selected-count');
        const deleteBtn = document.getElementById('delete-selected-btn');

        if (selectedCountEl) {
            selectedCountEl.textContent = `已选择 ${count} 项`;
        }

        if (deleteBtn) {
            deleteBtn.disabled = count === 0;
        }

        // 更新全选复选框
        const totalCheckboxes = document.querySelectorAll('.file-checkbox').length;
        const checkedCheckboxes = document.querySelectorAll('.file-checkbox:checked').length;
        const selectAll = document.getElementById('select-all');

        if (selectAll) {
            selectAll.checked = checkedCheckboxes === totalCheckboxes && totalCheckboxes > 0;
            selectAll.indeterminate = checkedCheckboxes > 0 && checkedCheckboxes < totalCheckboxes;
        }
    }

    clearSelection() {
        this.selectedFiles.clear();
        this.updateSelectionUI();
    }

    toggleSelectAll(checked) {
        document.querySelectorAll('.file-checkbox').forEach(cb => {
            cb.checked = checked;
            const path = cb.dataset.path;
            if (checked) {
                this.selectedFiles.add(path);
            } else {
                this.selectedFiles.delete(path);
            }
        });
        this.updateSelectionUI();
    }

    async deleteFiles(paths) {
        if (!paths || paths.length === 0) return;

        const message = paths.length === 1 ?
            `确定要删除 "${paths[0]}" 吗？` :
            `确定要删除选中的 ${paths.length} 项吗？`;

        if (!confirm(message)) {
            return;
        }

        try {
            const response = await fetch('/api/items', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    paths: JSON.stringify(paths)
                })
            });

            const result = await response.json();

            if (result.failed && result.failed.length > 0) {
                alert(`删除失败:\n${result.failed.map(f => f.path).join('\n')}`);
            }

            if (result.success && result.success.length > 0) {
                this.selectedFiles.clear();
                await this.loadFiles();
            }
        } catch (error) {
            console.error('Error deleting files:', error);
            alert('删除失败: ' + error.message);
        }
    }

    deleteSelected() {
        if (this.selectedFiles.size > 0) {
            this.deleteFiles(Array.from(this.selectedFiles));
        }
    }

    async downloadFile(path) {
        try {
            window.location.href = `/api/files/${encodeURIComponent(path)}`;
        } catch (error) {
            console.error('Error downloading file:', error);
            alert('下载失败');
        }
    }

    async previewFile(path) {
        const modal = document.getElementById('previewModal');
        const container = document.getElementById('previewContainer');

        if (!modal || !container) return;

        container.innerHTML = '<div class="loading">加载中...</div>';
        modal.style.display = 'flex';

        try {
            const response = await fetch(`/api/files/${encodeURIComponent(path)}?preview=true`);
            if (!response.ok) {
                throw new Error('Failed to load file');
            }

            const contentType = response.headers.get('content-type');
            const fileName = path.split('/').pop();
            const ext = fileName.split('.').pop().toLowerCase();

            if (contentType && contentType.startsWith('image/')) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                container.innerHTML = `<img src="${url}" class="preview-image" alt="${fileName}">`;
            } else if (contentType && contentType.startsWith('video/')) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                container.innerHTML = `<video src="${url}" class="preview-video" controls></video>`;
            } else if (contentType && contentType.startsWith('audio/')) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                container.innerHTML = `<audio src="${url}" class="preview-audio" controls></audio>`;
            } else if (contentType === 'application/pdf' || ext === 'pdf') {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                container.innerHTML = `<iframe src="${url}" class="preview-pdf"></iframe>`;
            } else if ((contentType && contentType.startsWith('text/')) || ['txt', 'js', 'css', 'html', 'json', 'xml', 'py', 'java', 'cpp', 'c', 'php'].includes(ext)) {
                const text = await response.text();
                container.innerHTML = `<pre class="preview-text">${this.escapeHtml(text)}</pre>`;
            } else {
                container.innerHTML = `
                    <div class="preview-unsupported">
                        <i class="fas fa-file"></i>
                        <p>无法预览此文件类型</p>
                        <button onclick="window.fileSystem.downloadFile('${path}')" class="btn-primary">
                            <i class="fas fa-download"></i> 下载文件
                        </button>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Preview error:', error);
            container.innerHTML = '<div class="error">预览失败</div>';
        }
    }

    showNewFolderModal() {
        const modal = document.getElementById('newFolderModal');
        const input = document.getElementById('folderName');
        if (modal && input) {
            modal.style.display = 'flex';
            input.value = '';
            input.focus();
        }
    }

    async createFolder() {
        const input = document.getElementById('folderName');
        if (!input) return;

        const name = input.value.trim();
        if (!name) {
            alert('请输入文件夹名称');
            return;
        }

        // 验证文件夹名称
        if (!/^[^\\/:*?"<>|]+$/.test(name)) {
            alert('文件夹名称包含非法字符');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('path', this.currentPath);
            formData.append('name', name);

            const response = await fetch('/api/folders', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                const modal = document.getElementById('newFolderModal');
                if (modal) {
                    modal.style.display = 'none';
                }
                await this.loadFiles();
            } else {
                alert('创建失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('Error creating folder:', error);
            alert('创建失败: ' + error.message);
        }
    }

    showPathModal() {
        const modal = document.getElementById('pathModal');
        const currentPathEl = document.getElementById('storage-path');
        const newPathInput = document.getElementById('newPath');
        const pathPreview = document.getElementById('pathPreview');

        if (modal && currentPathEl && newPathInput && pathPreview) {
            const currentPath = currentPathEl.textContent;
            newPathInput.value = currentPath;
            pathPreview.textContent = `预览: ${currentPath}`;
            modal.style.display = 'flex';
            setTimeout(() => newPathInput.focus(), 100);
        }
    }

    browseFolder() {
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.directory = true;
        input.multiple = false;

        input.onchange = (e) => {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                let folderPath = '';

                if (file.path) {
                    folderPath = file.path.substring(0, file.path.lastIndexOf('\\'));
                } else if (file.webkitRelativePath) {
                    const parts = file.webkitRelativePath.split('/');
                    if (parts.length > 0) {
                        alert('您的浏览器不支持获取完整文件夹路径。\n请手动输入完整路径，例如: D:\\shared_files');
                        return;
                    }
                }

                const newPathInput = document.getElementById('newPath');
                const pathPreview = document.getElementById('pathPreview');

                if (newPathInput && folderPath) {
                    newPathInput.value = folderPath;
                    if (pathPreview) {
                        pathPreview.textContent = `预览: ${folderPath}`;
                    }
                } else {
                    alert('请手动输入完整的文件夹路径');
                }
            }
        };

        input.click();
    }

    async updateStoragePath() {
        const newPathInput = document.getElementById('newPath');
        if (!newPathInput) return;

        let newPath = newPathInput.value.trim();
        if (!newPath) {
            alert('请输入路径');
            return;
        }

        newPath = newPath.replace(/^['"]|['"]$/g, '');

        if (navigator.platform.indexOf('Win') > -1) {
            newPath = newPath.replace(/\//g, '\\');
        } else {
            newPath = newPath.replace(/\\/g, '/');
        }

        if (navigator.platform.indexOf('Win') > -1) {
            if (!/^[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$/.test(newPath) &&
                !/^[a-zA-Z]:\\$/.test(newPath) &&
                !/^[a-zA-Z]:$/.test(newPath)) {
                if (!confirm('路径格式可能不正确，确定要继续吗？\n正确的格式例如: D:\\shared_files')) {
                    return;
                }
            }
        }

        const updateBtn = document.getElementById('updatePathBtn');
        const originalText = updateBtn.textContent;
        updateBtn.textContent = '更新中...';
        updateBtn.disabled = true;

        try {
            console.log('Updating storage path to:', newPath);

            const formData = new FormData();
            formData.append('new_path', newPath);

            const response = await fetch('/api/storage/path', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            console.log('Update path response:', data);

            if (data.success) {
                const storagePath = document.getElementById('storage-path');
                if (storagePath) {
                    storagePath.textContent = newPath;
                    storagePath.title = newPath;
                }

                const modal = document.getElementById('pathModal');
                if (modal) {
                    modal.style.display = 'none';
                }

                await this.loadFiles('');

                const storageResponse = await fetch('/api/storage');
                if (storageResponse.ok) {
                    const storageInfo = await storageResponse.json();
                    this.updateStorageDisplay(storageInfo);
                }

                alert('存储路径更新成功！');
            } else {
                alert('更新失败，请确保路径存在且有写入权限：' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('Error updating path:', error);
            alert('更新失败: ' + error.message);
        } finally {
            updateBtn.textContent = originalText;
            updateBtn.disabled = false;
        }
    }

    uploadFiles() {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            const uploadPromises = files.map(file =>
                this.uploadFile(file, this.currentPath)
            );

            const queue = document.getElementById('uploadQueue');
            if (queue) {
                queue.style.display = 'block';
            }

            // 等待所有上传完成
            Promise.all(uploadPromises).then(() => {
                this.loadFiles(); // 所有文件上传完成后刷新
            });
        };
        input.click();
    }

    uploadFolder() {
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.multiple = true;
        input.onchange = (e) => {
            const files = Array.from(e.target.files);

            if (files.length === 0) return;

            // 获取根文件夹名称
            const firstFile = files[0];
            let rootFolderName = '';

            if (firstFile.webkitRelativePath) {
                rootFolderName = firstFile.webkitRelativePath.split('/')[0];
            }

            const queue = document.getElementById('uploadQueue');
            if (queue) {
                queue.style.display = 'block';
            }

            console.log(`开始上传文件夹: ${rootFolderName}, 包含 ${files.length} 个文件`);

            // 上传文件夹
            this.uploadFolderStructure(files, this.currentPath).then(() => {
                console.log('文件夹上传完成');
                this.loadFiles();
            }).catch(error => {
                console.error('文件夹上传失败:', error);
                alert('文件夹上传失败: ' + error.message);
            });
        };
        input.click();
    }

    async uploadFolderStructure(files, basePath) {
        // 按路径分组文件
        const fileGroups = {};

        for (const file of files) {
            const relativePath = file.webkitRelativePath;
            const pathParts = relativePath.split('/');
            const fileName = pathParts.pop();
            const folderPath = pathParts.join('/');

            if (!fileGroups[folderPath]) {
                fileGroups[folderPath] = [];
            }
            fileGroups[folderPath].push({
                file: file,
                name: fileName,
                path: folderPath
            });
        }

        // 首先创建所有必要的文件夹
        const folderPaths = Object.keys(fileGroups);
        for (const folderPath of folderPaths) {
            if (folderPath) {
                const targetFolderPath = basePath ? `${basePath}/${folderPath}` : folderPath;
                try {
                    await this.createFolderAtPath(targetFolderPath);
                } catch (error) {
                    console.warn(`创建文件夹失败 ${targetFolderPath}:`, error);
                }
            }
        }

        // 然后上传所有文件
        const uploadPromises = [];
        for (const folderPath of folderPaths) {
            const filesInFolder = fileGroups[folderPath];
            for (const fileInfo of filesInFolder) {
                const targetPath = basePath ?
                    (folderPath ? `${basePath}/${folderPath}` : basePath) :
                    folderPath;

                uploadPromises.push(
                    this.uploadFile(fileInfo.file, targetPath)
                );
            }
        }

        return Promise.all(uploadPromises);
    }

    async createFolderAtPath(folderPath) {
        if (!folderPath) return true;

        const parts = folderPath.split('/');
        let currentPath = '';

        for (const part of parts) {
            if (!part) continue;

            currentPath = currentPath ? `${currentPath}/${part}` : part;

            try {
                const formData = new FormData();
                const parentPath = currentPath.includes('/') ?
                    currentPath.substring(0, currentPath.lastIndexOf('/')) : '';
                formData.append('path', parentPath);
                formData.append('name', part);

                const response = await fetch('/api/folders', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (!data.success) {
                    console.warn(`创建文件夹 ${currentPath} 可能已存在`);
                }
            } catch (error) {
                console.warn(`创建文件夹 ${currentPath} 出错:`, error);
            }
        }

        return true;
    }

    async uploadFile(file, targetPath) {
    const fileId = this.generateFileId();
    const chunkSize = 8 * 1024 * 1024; // 8MB
    const totalChunks = Math.ceil(file.size / chunkSize);

    console.log(`Uploading file: ${file.name}, targetPath: '${targetPath}', totalChunks: ${totalChunks}`);

    // 添加到队列 UI
    this.addToQueue(fileId, file.name, file.size, totalChunks);

    try {
        // 1. 初始化上传 - 使用 FormData 而不是 URLSearchParams
        const formData = new FormData();
        formData.append('file_id', fileId);
        formData.append('file_name', file.name);
        formData.append('file_size', file.size.toString());

        // 关键修复：确保 target_path 总是被发送，但正确处理空值
        // 如果 targetPath 是空字符串、null、undefined、'/' 或 '\'，发送空字符串
        let finalTargetPath = '';
        if (targetPath && targetPath !== '/' && targetPath !== '\\') {
            finalTargetPath = targetPath;
        }
        formData.append('target_path', finalTargetPath);
        formData.append('total_chunks', totalChunks.toString());

        console.log('Init upload FormData contents:');
        for (let pair of formData.entries()) {
            console.log(pair[0] + ': ' + pair[1]);
        }

        const initResponse = await fetch('/api/upload/init', {
            method: 'POST',
            // 不要手动设置 Content-Type，让浏览器自动设置带有 boundary 的 multipart/form-data
            // headers: {
            //     'Content-Type': 'application/x-www-form-urlencoded',
            // },
            body: formData
        });

        if (!initResponse.ok) {
            const errorText = await initResponse.text();
            console.error('Init upload failed:', initResponse.status, errorText);

            // 尝试解析错误响应
            try {
                const errorJson = JSON.parse(errorText);
                throw new Error(`Failed to initialize upload: ${errorJson.detail || errorText}`);
            } catch (e) {
                throw new Error(`Failed to initialize upload: ${initResponse.status} ${errorText}`);
            }
        }

        const initData = await initResponse.json();
        console.log('Init upload response:', initData);

        if (initData.error) {
            throw new Error(initData.error);
        }

        // 确保 uploaded_chunks 是数组
        const uploadedChunks = Array.isArray(initData.uploaded_chunks) ?
            initData.uploaded_chunks : [];

        this.updateQueueProgress(fileId, uploadedChunks.length, totalChunks);

        // 2. 分片上传循环
        for (let i = 0; i < totalChunks; i++) {
            // 跳过已上传的分片
            if (uploadedChunks.includes(i)) {
                console.log(`Chunk ${i} already uploaded, skipping`);
                continue;
            }

            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);

            const chunkFormData = new FormData();
            chunkFormData.append('file_id', fileId);
            chunkFormData.append('chunk_index', i.toString());
            chunkFormData.append('chunk_data', chunk);

            console.log(`Uploading chunk ${i}/${totalChunks-1}, size: ${chunk.size}`);

            const response = await fetch('/api/upload/chunk', {
                method: 'POST',
                body: chunkFormData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to upload chunk ${i}: ${response.status} ${errorText}`);
            }

            const data = await response.json();
            console.log(`Chunk ${i} response:`, data);

            if (data.error) {
                throw new Error(data.error);
            }

            // 更新进度
            const currentUploadedCount = Array.isArray(data.uploaded_chunks) ?
                data.uploaded_chunks.length :
                (data.uploaded_chunks || i + 1);

            this.updateQueueProgress(fileId, currentUploadedCount, data.total_chunks || totalChunks);

            // 如果完成，跳出循环
            if (data.completed) {
                console.log('Upload completed from server response');
                break;
            }
        }

        // 3. 标记上传完成
        this.updateQueueProgress(fileId, totalChunks, totalChunks);

        // 延迟移除，让用户看到100%状态
        setTimeout(() => {
            this.removeFromQueue(fileId);
            this.checkAndCloseQueue();
        }, 1000);

        // 刷新文件列表
        await this.loadFiles();

    } catch (error) {
        console.error('Upload error:', error);
        this.updateQueueError(fileId, error.message);

        // 出错时延迟移除
        setTimeout(() => {
            this.removeFromQueue(fileId);
            this.checkAndCloseQueue();
        }, 3000);
    }
}

    generateFileId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    addToQueue(fileId, fileName, fileSize, totalChunks) {
        const queue = document.getElementById('queueItems');
        if (!queue) return;

        this.pendingUploads++;

        const size = this.formatFileSize(fileSize);

        const itemHtml = `
            <div class="queue-item" id="queue-${fileId}">
                <div class="item-info">
                    <div class="file-info">
                        <i class="fas fa-file"></i>
                        <span class="file-name" title="${fileName}">${this.escapeHtml(fileName)}</span>
                    </div>
                    <span class="file-size">${size}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar" style="width: 0%"></div>
                </div>
                <div class="item-status">
                    <span class="status-text">准备上传...</span>
                    <span class="progress-text">0/${totalChunks}</span>
                </div>
                <button class="cancel-upload" onclick="window.fileSystem.cancelUpload('${fileId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        queue.insertAdjacentHTML('beforeend', itemHtml);
        this.uploads.set(fileId, {
            fileName,
            totalChunks,
            uploadedChunks: 0,
            status: 'uploading'
        });
    }

    updateQueueProgress(fileId, uploadedChunks, totalChunks) {
        const item = document.getElementById(`queue-${fileId}`);
        if (!item) return;

        const uploadedCount = typeof uploadedChunks === 'number' ? uploadedChunks : 0;
        const totalCount = typeof totalChunks === 'number' ? totalChunks : 1;
        const safeTotal = totalCount === 0 ? 1 : totalCount;

        const percentage = Math.min(100, Math.round((uploadedCount / safeTotal) * 100));

        const progressBar = item.querySelector('.progress-bar');
        const statusText = item.querySelector('.status-text');
        const progressText = item.querySelector('.progress-text');

        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }

        if (statusText) {
            if (percentage >= 100) {
                statusText.textContent = '已完成';
                statusText.style.color = 'var(--success-color)';
            } else {
                statusText.textContent = '上传中...';
                statusText.style.color = '';
            }
        }

        if (progressText) {
            progressText.textContent = `${uploadedCount}/${totalCount}`;
        }
    }

    updateQueueError(fileId, error) {
        const item = document.getElementById(`queue-${fileId}`);
        if (!item) return;

        const statusText = item.querySelector('.status-text');
        const progressBar = item.querySelector('.progress-bar');

        if (statusText) {
            statusText.textContent = '失败';
            statusText.style.color = 'var(--danger-color)';
        }

        if (progressBar) {
            progressBar.style.background = 'var(--danger-color)';
        }

        item.setAttribute('title', error);

        setTimeout(() => {
            this.removeFromQueue(fileId);
            this.checkAndCloseQueue();
        }, 3000);
    }

    removeFromQueue(fileId) {
        const item = document.getElementById(`queue-${fileId}`);
        if (item) {
            item.remove();
        }
        this.uploads.delete(fileId);
        this.pendingUploads--;
        this.checkAndCloseQueue();
    }

    checkAndCloseQueue() {
        const queueItemsContainer = document.getElementById('queueItems');
        const uploadQueueWindow = document.getElementById('uploadQueue');

        if (!queueItemsContainer || !uploadQueueWindow) return;

        const hasNoPendingTasks = this.pendingUploads <= 0;
        const isDomEmpty = queueItemsContainer.children.length === 0;

        if (hasNoPendingTasks && isDomEmpty) {
            setTimeout(() => {
                if (this.pendingUploads <= 0 && queueItemsContainer.children.length === 0) {
                    uploadQueueWindow.style.display = 'none';
                    const icon = document.querySelector('#minimize-queue i');
                    if(icon) icon.className = 'fas fa-minus';
                }
            }, 500);
        }
    }

    cancelUpload(fileId) {
        if (confirm('确定要取消上传吗？')) {
            fetch(`/api/upload/${fileId}`, {
                method: 'DELETE'
            }).then(() => {
                this.removeFromQueue(fileId);
                this.checkAndCloseQueue();
            }).catch(error => {
                console.error('Error cancelling upload:', error);
            });
        }
    }

    updateStorageDisplay(info) {
        const usedGB = info.used_gb || 0;
        const freeGB = info.free_gb || 0;
        const totalGB = info.total_gb || 100;
        const percentage = info.percentage || 0;

        const usedSpace = document.getElementById('used-space');
        const freeSpace = document.getElementById('free-space');
        const totalSpace = document.getElementById('total-space');
        const storagePercentage = document.getElementById('storage-percentage');
        const storageBar = document.querySelector('.storage-used');
        const pathElement = document.getElementById('storage-path');

        if (usedSpace) usedSpace.textContent = `${usedGB.toFixed(2)} GB`;
        if (freeSpace) freeSpace.textContent = `${freeGB.toFixed(2)} GB`;
        if (totalSpace) totalSpace.textContent = `${totalGB.toFixed(2)} GB`;
        if (storagePercentage) storagePercentage.textContent = `${percentage.toFixed(1)}%`;

        if (storageBar) {
            storageBar.style.width = `${percentage}%`;

            if (percentage > 90) {
                storageBar.style.background = 'linear-gradient(90deg, #ef476f, #ff6b6b)';
            } else if (percentage > 70) {
                storageBar.style.background = 'linear-gradient(90deg, #ffd166, #ffb347)';
            } else {
                storageBar.style.background = 'linear-gradient(90deg, var(--primary-color), #667eea)';
            }
        }

        if (pathElement && info.storage_path) {
            pathElement.textContent = info.storage_path;
            pathElement.title = info.storage_path;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word',
            'docx': 'fa-file-word',
            'xls': 'fa-file-excel',
            'xlsx': 'fa-file-excel',
            'ppt': 'fa-file-powerpoint',
            'pptx': 'fa-file-powerpoint',
            'txt': 'fa-file-alt',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'gif': 'fa-file-image',
            'bmp': 'fa-file-image',
            'svg': 'fa-file-image',
            'webp': 'fa-file-image',
            'mp4': 'fa-file-video',
            'avi': 'fa-file-video',
            'mkv': 'fa-file-video',
            'mov': 'fa-file-video',
            'wmv': 'fa-file-video',
            'flv': 'fa-file-video',
            'mp3': 'fa-file-audio',
            'wav': 'fa-file-audio',
            'flac': 'fa-file-audio',
            'aac': 'fa-file-audio',
            'ogg': 'fa-file-audio',
            'zip': 'fa-file-archive',
            'rar': 'fa-file-archive',
            '7z': 'fa-file-archive',
            'tar': 'fa-file-archive',
            'gz': 'fa-file-archive',
            'html': 'fa-file-code',
            'css': 'fa-file-code',
            'js': 'fa-file-code',
            'json': 'fa-file-code',
            'xml': 'fa-file-code',
            'py': 'fa-file-code',
            'java': 'fa-file-code',
            'cpp': 'fa-file-code',
            'c': 'fa-file-code',
            'php': 'fa-file-code'
        };

        return icons[ext] || 'fa-file';
    }

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.fileSystem = new FileShareSystem();
});