// 全局JavaScript函数

// 全选/取消全选功能
function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="selected_items"]');
    const selectAllCheckbox = document.getElementById('select_all');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

// 全选/取消全选功能（数据仓库）
function toggleSelectAllWarehouse() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="selected_data"]');
    const selectAllCheckbox = document.getElementById('select_all_warehouse');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

// 检查是否有选中项
function hasSelectedItems() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="selected_items"]:checked');
    return checkboxes.length > 0;
}

// 检查是否有选中项（数据仓库）
function hasSelectedWarehouseItems() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="selected_data"]:checked');
    return checkboxes.length > 0;
}

// 批量保存数据
function saveSelectedData() {
    if (!hasSelectedItems()) {
        alert('请选择要保存的数据');
        return;
    }
    
    if (confirm('确定要保存选中的数据到数据仓库吗？')) {
        document.getElementById('save_form').submit();
    }
}

// 生成PDF报告
function generatePDFReport() {
    if (!hasSelectedWarehouseItems()) {
        alert('请选择要生成报告的数据');
        return;
    }
    
    if (confirm('确定要生成PDF报告吗？')) {
        document.getElementById('pdf_form').submit();
    }
}

// 下载PDF文件
function downloadPDF(pdfUrl) {
    window.open(pdfUrl, '_blank');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 为搜索表单添加提交处理
    const searchForm = document.getElementById('search_form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const keywords = document.getElementById('keywords').value;
            if (!keywords.trim()) {
                alert('请输入搜索关键词');
                e.preventDefault();
                return;
            }
            
            const pages = document.getElementById('pages');
            if (pages && (isNaN(pages.value) || pages.value < 1)) {
                alert('请输入有效的页数（至少1页）');
                e.preventDefault();
                return;
            }
        });
    }
    
    // 为数据仓库搜索表单添加提交处理
    const warehouseSearchForm = document.getElementById('warehouse_search_form');
    if (warehouseSearchForm) {
        warehouseSearchForm.addEventListener('submit', function(e) {
            // 可以在这里添加额外的验证逻辑
        });
    }
    
    // 为链接添加点击确认（可选）
    const resultLinks = document.querySelectorAll('.data-item h3 a');
    resultLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 如果需要在新窗口打开，可以取消注释下面的代码
            // e.preventDefault();
            // window.open(this.href, '_blank');
        });
    });
    
    // 为全选复选框添加事件监听
    const selectAllCheckbox = document.getElementById('select_all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', toggleSelectAll);
    }
    
    const selectAllWarehouseCheckbox = document.getElementById('select_all_warehouse');
    if (selectAllWarehouseCheckbox) {
        selectAllWarehouseCheckbox.addEventListener('change', toggleSelectAllWarehouse);
    }
});

// 显示消息提示（可选，用于增强用户体验）
function showMessage(message, type = 'success') {
    // 创建消息元素
    const messageDiv = document.createElement('div');
    messageDiv.className = `flash-message ${type}`;
    messageDiv.textContent = message;
    
    // 添加到页面
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(messageDiv, container.firstChild);
        
        // 3秒后自动移除
        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }
}