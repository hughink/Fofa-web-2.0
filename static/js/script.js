// 等待 DOM 内容加载完毕后执行
document.addEventListener('DOMContentLoaded', () => {
    // 侧边栏切换按钮
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');

    // 切换侧边栏显示状态
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('is-hidden'); // 切换侧边栏的显示状态
        overlay.classList.toggle('is-active'); // 切换覆盖层的状态
    });

    // 点击覆盖层时隐藏侧边栏
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.add('is-hidden'); // 隐藏侧边栏
            overlay.classList.remove('is-active'); // 移除覆盖层的激活状态
        });
    }

    // 删除通知按钮功能
    const deleteButtons = document.querySelectorAll('.notification .delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', () => {
            button.parentElement.classList.add('is-hidden'); // 隐藏通知
        });
    });

    // Navbar 菜单按钮功能（移动端）
    const navbarBurgers = Array.from(document.querySelectorAll('.navbar-burger'));
    navbarBurgers.forEach(el => {
        el.addEventListener('click', () => {
            const target = el.dataset.target; // 获取要切换的目标元素
            const targetElement = document.getElementById(target);

            el.classList.toggle('is-active'); // 切换菜单按钮的激活状态
            targetElement.classList.toggle('is-active'); // 切换目标元素的激活状态
        });
    });

    // 处理查询参数的填充
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query'); // 获取 URL 中的查询参数

    // 将查询参数填充到输入框
    if (query) {
        document.getElementById('queryInput').value = decodeURIComponent(query); // 解码并填入输入框
    }

    // 初始化 DataTable
    $(document).ready(function() {
        // 检查并销毁现有 DataTable 实例
        if ($.fn.DataTable.isDataTable('#resultsTable')) {
            $('#resultsTable').DataTable().destroy();
        }

        // 初始化 DataTable
        $('#resultsTable').DataTable({
            "paging": true,
            "ordering": true,
            "info": true,
            "searching": true,
            "pageLength": 50,
            "lengthMenu": [[50, 100, 200, 500, 1000], [50, 100, 200, 500, 1000]]
        });

        // 自定义右键菜单
        $.contextMenu({
            selector: '#resultsTable tbody td',
            items: {
                "copy": {
                    name: "复制整列数据",
                    callback: function(key, options) {
                        const columnData = [];
                        const rows = document.querySelectorAll('#resultsTable tbody tr');
                        rows.forEach(row => {
                            columnData.push(row.cells[options.$trigger[0].cellIndex].innerText);
                        });
                        const textToCopy = columnData.join('\n');
                        navigator.clipboard.writeText(textToCopy).then(() => {
                            showTemporaryAlert('整列数据已复制到剪切板', 1000);
                        });
                    }
                },
                "copy_unique": {
                    name: "复制整列并去重",
                    callback: function(key, options) {
                        const columnData = [];
                        const uniqueData = new Set(); // 使用 Set 去重
                        const rows = document.querySelectorAll('#resultsTable tbody tr');
                        rows.forEach(row => {
                            uniqueData.add(row.cells[options.$trigger[0].cellIndex].innerText);
                        });
                        const textToCopy = Array.from(uniqueData).join('\n');
                        navigator.clipboard.writeText(textToCopy).then(() => {
                            showTemporaryAlert('整列数据已去重并复制到剪切板', 1000);
                        });
                    }
                },
                "open": {
                    name: "在新标签页中打开",
                    callback: function(key, options) {
                        const currentCell = options.$trigger[0];
                        if (currentCell.cellIndex === 1) { // 仅针对“主机”列
                            const url = currentCell.innerText;
                            if (url.startsWith('http')) {
                                window.open(url, '_blank');
                            } else {
                                window.open('http://' + url, '_blank');
                                window.open('https://' + url, '_blank');
                            }
                        }
                    }
                },
                "sep1": "---------",
                "quit": {
                    name: "关闭菜单",
                    callback: function() {
                        $.contextMenu("hide");
                    }
                }
            }
        });
    });

    // 显示临时提示
    function showTemporaryAlert(message, duration) {
        const alert = document.createElement('div');
        alert.innerText = message;
        alert.style.position = 'fixed';
        alert.style.bottom = '10px';
        alert.style.right = '10px';
        alert.style.backgroundColor = '#000';
        alert.style.color = '#fff';
        alert.style.padding = '10px';
        alert.style.borderRadius = '5px';
        alert.style.zIndex = '1000';
        document.body.appendChild(alert);
        setTimeout(() => {
            document.body.removeChild(alert);
        }, duration);
    }

    // 切换查询语法参考的显示状态
    document.getElementById('toggleSyntaxBtn').addEventListener('click', function() {
        const dropdown = document.getElementById('syntaxDropdown');
        dropdown.classList.toggle('is-hidden');
    });

    // 复制文本到剪贴板
    window.copyToClipboard = function(element) {
        const text = element.innerText;  // 获取单元格的文本
        const tempInput = document.createElement('input');  // 创建一个临时输入框
        tempInput.value = text;  // 设置输入框的值为要复制的文本
        document.body.appendChild(tempInput);  // 将输入框添加到文档中
        tempInput.select();  // 选中输入框的内容
        document.execCommand('copy');  // 执行复制命令
        document.body.removeChild(tempInput);  // 移除临时输入框
        showTemporaryAlert('已复制到剪贴板: ' + text, 1000);  // 显示复制成功的提示
    };

    // 处理表单提交
    window.handleSubmit = function(event) {
        event.preventDefault();
        const query = document.getElementById("queryInput").value;
        localStorage.setItem('queryInput', query); // 存储查询
        event.target.submit();
    };
});
