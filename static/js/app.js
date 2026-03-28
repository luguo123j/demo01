// Novel Crawler Application JavaScript

let currentTaskId = null;
let currentFilename = null;
let progressCheckInterval = null;
let isPaused = false;
let isStopped = false;
let pendingNovel = null;

// Search novel function
async function searchNovel() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const searchStatus = document.getElementById('searchStatus');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');

    const keyword = searchInput.value.trim();

    if (!keyword) {
        showAlert('请输入小说名称', 'error');
        return;
    }

    // Disable search button and show loading
    searchBtn.disabled = true;
    searchStatus.textContent = '搜索中...';
    searchStatus.className = 'status-text info';
    resultsSection.classList.add('hidden');

    try {
        const response = await fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '搜索失败');
        }

        const data = await response.json();

        if (data.success && data.novels && data.novels.length > 0) {
            renderResults(data.novels);
            const sourceSummary = buildSourceSummary(data.sources || []);
            const degradedSuffix = data.partial_success ? `，部分来源异常：${data.degraded_reason || '已自动降级'}` : '';
            searchStatus.textContent = `找到 ${data.novels.length} 本小说（${sourceSummary}）${degradedSuffix}`;
            searchStatus.className = 'status-text success';
        } else {
            showAlert(`没有找到与"${keyword}"相关的小说`, 'error');
            searchStatus.textContent = '未找到结果';
            searchStatus.className = 'status-text error';
        }

    } catch (error) {
        console.error('Search error:', error);
        showAlert(`搜索出错: ${error.message}`, 'error');
        searchStatus.textContent = '搜索失败';
        searchStatus.className = 'status-text error';
    } finally {
        searchBtn.disabled = false;
    }
}

function buildSourceSummary(sources) {
    if (!sources || sources.length === 0) {
        return '未返回来源信息';
    }

    const okCount = sources.filter(source => source.success).length;
    return `${okCount}/${sources.length} 来源可用`;
}

// Render search results
function renderResults(novels) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');

    resultsContainer.innerHTML = '';

    novels.forEach((novel, index) => {
        const card = document.createElement('div');
        card.className = 'novel-card';

        const title = document.createElement('div');
        title.className = 'novel-title';
        title.textContent = novel.title;

        const author = document.createElement('div');
        author.className = 'novel-author';
        author.textContent = `作者: ${novel.author || '未知'}`;

        const desc = document.createElement('div');
        desc.className = 'novel-desc';
        desc.textContent = novel.description || '暂无简介';

        const source = document.createElement('div');
        source.className = 'novel-author';
        source.textContent = `来源: ${novel.source_name || novel.source_id || '默认源'}`;

        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-btn';
        downloadBtn.textContent = '下载';
        downloadBtn.onclick = () => showChapterRangeModal(novel);

        card.appendChild(title);
        card.appendChild(author);
        card.appendChild(source);
        card.appendChild(desc);
        card.appendChild(downloadBtn);
        resultsContainer.appendChild(card);
    });

    resultsSection.classList.remove('hidden');
}

// Show chapter range modal
function showChapterRangeModal(novel) {
    pendingNovel = novel;
    const modal = document.getElementById('chapterRangeModal');
    modal.classList.remove('hidden');
}

// Close chapter range modal
function closeChapterRangeModal() {
    const modal = document.getElementById('chapterRangeModal');
    modal.classList.add('hidden');
}

// Confirm chapter range
function confirmChapterRange() {
    const startChapter = parseInt(document.getElementById('startChapter').value) || 1;
    const endChapterInput = document.getElementById('endChapter').value;
    const endChapter = endChapterInput ? parseInt(endChapterInput) : null;

    closeChapterRangeModal();

    if (pendingNovel && pendingNovel.url) {
        downloadNovel(pendingNovel.url, startChapter, endChapter, pendingNovel.source_id || null);
    }
}

// Download novel function
async function downloadNovel(novelUrl, startChapter = 1, endChapter = null, sourceId = null) {
    const progressSection = document.getElementById('progressSection');
    const downloadComplete = document.getElementById('downloadComplete');

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                novel_url: novelUrl,
                start_chapter: startChapter,
                end_chapter: endChapter,
                source_id: sourceId
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '下载请求失败');
        }

        const data = await response.json();

        if (data.success && data.task_id) {
            currentTaskId = data.task_id;
            currentFilename = null;
            isPaused = false;
            isStopped = false;

            // Show progress section
            progressSection.classList.remove('hidden');
            downloadComplete.classList.add('hidden');

            // Reset progress display
            document.getElementById('progressTitle').textContent = '下载中...';
            document.getElementById('progressDetails').textContent = '准备下载';
            document.getElementById('progressBar').style.width = '0%';
            document.getElementById('progressPercentage').textContent = '0%';

            // Update control buttons
            updateControlButtons();

            // Start checking progress
            checkProgress(data.task_id);
        } else {
            showAlert('下载任务创建失败', 'error');
        }

    } catch (error) {
        console.error('Download error:', error);
        showAlert(`下载出错: ${error.message}`, 'error');
    }
}

// Update control buttons
function updateControlButtons() {
    const pauseBtn = document.getElementById('pauseBtn');
    const stopBtn = document.getElementById('stopBtn');

    if (isPaused) {
        pauseBtn.textContent = '继续下载';
        pauseBtn.classList.remove('pause-btn');
        pauseBtn.classList.add('resume-btn');
    } else {
        pauseBtn.textContent = '暂停下载';
        pauseBtn.classList.remove('resume-btn');
        pauseBtn.classList.add('pause-btn');
    }

    // Enable/disable based on download status
    const canControl = currentTaskId && !isStopped;
    pauseBtn.disabled = !canControl;
    stopBtn.disabled = !canControl;
}

// Pause download
async function pauseDownload() {
    if (!currentTaskId) {
        return;
    }

    try {
        const response = await fetch(`/api/pause/${currentTaskId}`, {
            method: 'POST'
        });

        if (response.ok) {
            isPaused = !isPaused;
            if (isPaused) {
                showAlert('下载已暂停', 'info');
            } else {
                showAlert('继续下载', 'info');
            }
            updateControlButtons();
        }
    } catch (error) {
        console.error('Pause error:', error);
        showAlert('暂停/继续操作失败', 'error');
    }
}

// Stop download
async function stopDownload() {
    if (!currentTaskId) {
        return;
    }

    try {
        const response = await fetch(`/api/stop/${currentTaskId}`, {
            method: 'POST'
        });

        if (response.ok) {
            isStopped = true;
            isPaused = false;

            // Stop progress checking
            if (progressCheckInterval) {
                clearInterval(progressCheckInterval);
                progressCheckInterval = null;
            }

            showAlert('下载已停止', 'info');
            updateControlButtons();
            document.getElementById('progressDetails').textContent = '下载已停止';
        }
    } catch (error) {
        console.error('Stop error:', error);
        showAlert('停止操作失败', 'error');
    }
}

// Check download progress
function checkProgress(taskId) {
    // Clear existing interval
    if (progressCheckInterval) {
        clearInterval(progressCheckInterval);
    }

    // Start polling
    progressCheckInterval = setInterval(async () => {
        if (isStopped) {
            return;
        }

        if (isPaused) {
            return;
        }

        try {
            const response = await fetch(`/api/status/${taskId}`);

            if (!response.ok) {
                throw new Error('获取下载状态失败');
            }

            const data = await response.json();

            if (data.success && data.status) {
                updateProgress(data.status);

                // Check if download is complete
                if (data.status.status === 'completed') {
                    clearInterval(progressCheckInterval);
                    progressCheckInterval = null;

                    if (data.status.result && data.status.result.filename) {
                        currentFilename = data.status.result.filename;
                    }
                }

                // Check if download failed
                if (data.status.status === 'error') {
                    clearInterval(progressCheckInterval);
                    progressCheckInterval = null;
                    showAlert(`下载失败: ${data.status.error || '未知错误'}`, 'error');
                }
            }

        } catch (error) {
            console.error('Progress check error:', error);
            clearInterval(progressCheckInterval);
            progressCheckInterval = null;
        }
    }, 2000); // Check every 2 seconds
}

// Update progress display
function updateProgress(status) {
    const progressTitle = document.getElementById('progressTitle');
    const progressDetails = document.getElementById('progressDetails');
    const progressBar = document.getElementById('progressBar');
    const progressPercentage = document.getElementById('progressPercentage');
    const downloadComplete = document.getElementById('downloadComplete');

    if (status.novel_title) {
        progressTitle.textContent = status.novel_title;
    }

    if (status.status === 'downloading') {
        const downloaded = status.downloaded_chapters || 0;
        const total = status.total_chapters || 0;

        if (total > 0) {
            progressDetails.textContent = `已下载 ${downloaded} / ${total} 章`;
        } else {
            progressDetails.textContent = '正在下载...';
        }
    } else if (status.status === 'completed') {
        progressDetails.textContent = '下载完成';
        downloadComplete.classList.remove('hidden');
    } else if (status.status === 'error') {
        progressDetails.textContent = '下载失败';
    }

    if (status.progress !== undefined) {
        progressBar.style.width = `${status.progress}%`;
        progressPercentage.textContent = `${status.progress}%`;
    }
}

// Download file
function downloadFile() {
    if (currentFilename) {
        window.location.href = `/api/download/${currentFilename}`;
    } else {
        showAlert('文件不可用', 'error');
    }
}

// Load download history
async function loadHistory() {
    const historyContainer = document.getElementById('historyContainer');

    try {
        const response = await fetch('/api/history');

        if (!response.ok) {
            throw new Error('获取下载历史失败');
        }

        const data = await response.json();

        if (data.success && data.history) {
            renderHistory(data.history);
        } else {
            historyContainer = document.createElement('p');
            historyContainer.className = 'empty-message';
            historyContainer.textContent = '暂无下载历史';
        }

    } catch (error) {
        console.error('History load error:', error);
        const historyContainer = document.getElementById('historyContainer');
        historyContainer.innerHTML = '<p class="empty-message">加载历史失败</p>';
    }
}

// Render download history
function renderHistory(history) {
    const historyContainer = document.getElementById('historyContainer');

    if (history.length === 0) {
        historyContainer.innerHTML = '<p class="empty-message">暂无下载历史</p>';
        return;
    }

    historyContainer.innerHTML = '';

    // Show most recent first
    const reversedHistory = [...history].reverse();

    reversedHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';

        const title = document.createElement('div');
        title.className = 'history-item-title';
        title.textContent = item.novel_title || '未知小说';

        const meta = document.createElement('div');
        meta.className = 'history-item-meta';
        const chapters = item.chapter_count ? `${item.chapter_count}章` : '未知章数';
        const source = item.source_id ? `来源:${item.source_id}` : '来源:默认';
        meta.textContent = `${chapters} - ${source} - ${item.download_time || '未知时间'}`;

        historyItem.appendChild(title);
        historyItem.appendChild(meta);
        historyContainer.appendChild(historyItem);
    });
}

// Show alert modal
function showAlert(message, type = 'info') {
    const modal = document.getElementById('alertModal');
    const alertTitle = document.getElementById('alertTitle');
    const alertMessage = document.getElementById('alertMessage');

    if (type === 'error') {
        alertTitle.textContent = '错误';
        alertTitle.style.color = '#dc3545';
    } else {
        alertTitle.textContent = '提示';
        alertTitle.style.color = '#333';
    }

    alertMessage.textContent = message;
    modal.classList.remove('hidden');
}

// Close alert modal
function closeAlert() {
    const modal = document.getElementById('alertModal');
    modal.classList.add('hidden');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load download history
    loadHistory();

    // Enable search on Enter key
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchNovel();
        }
    });
});

// Close modals on background click
document.getElementById('alertModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeAlert();
    }
});

document.getElementById('chapterRangeModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeChapterRangeModal();
    }
});
