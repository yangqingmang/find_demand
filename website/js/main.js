// 主要JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initNavigation();
    initSearch();
    initToolCards();
    initScrollEffects();
    initMobileMenu();
});

// 导航功能
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有活动状态
            navLinks.forEach(l => l.classList.remove('active'));
            
            // 添加当前活动状态
            this.classList.add('active');
            
            // 滚动到对应部分
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 搜索功能
function initSearch() {
    const searchInputs = document.querySelectorAll('.search-input, .hero-search-input');
    const searchButtons = document.querySelectorAll('.search-btn, .hero-search-btn');
    
    // 搜索输入框事件
    searchInputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch(this.value);
            }
        });
        
        input.addEventListener('input', function() {
            if (this.value.length > 2) {
                showSearchSuggestions(this.value);
            } else {
                hideSearchSuggestions();
            }
        });
    });
    
    // 搜索按钮事件
    searchButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling || this.parentElement.querySelector('input');
            if (input) {
                performSearch(input.value);
            }
        });
    });
}

// 执行搜索
function performSearch(query) {
    if (!query.trim()) return;
    
    console.log('搜索:', query);
    
    // 显示加载状态
    showLoadingState();
    
    // 模拟搜索API调用
    setTimeout(() => {
        const results = mockSearchResults(query);
        displaySearchResults(results);
        hideLoadingState();
    }, 1000);
}

// 模拟搜索结果
function mockSearchResults(query) {
    const allTools = [
        { name: 'ChatGPT', category: 'AI聊天助手', rating: 4.8, description: 'OpenAI开发的强大对话AI' },
        { name: 'Claude', category: 'AI聊天助手', rating: 4.7, description: 'Anthropic开发的安全可靠的AI助手' },
        { name: 'Midjourney', category: 'AI图像生成', rating: 4.9, description: '顶级AI图像生成工具' },
        { name: 'GitHub Copilot', category: 'AI编程助手', rating: 4.6, description: 'AI编程助手' },
        { name: 'Jasper AI', category: 'AI写作助手', rating: 4.5, description: 'AI写作工具' }
    ];
    
    return allTools.filter(tool => 
        tool.name.toLowerCase().includes(query.toLowerCase()) ||
        tool.category.toLowerCase().includes(query.toLowerCase()) ||
        tool.description.toLowerCase().includes(query.toLowerCase())
    );
}

// 显示搜索建议
function showSearchSuggestions(query) {
    const suggestions = [
        'ChatGPT', 'Claude', 'Midjourney', 'GitHub Copilot', 'Jasper AI',
        'AI聊天助手', 'AI图像生成', 'AI写作助手', 'AI编程助手'
    ].filter(item => item.toLowerCase().includes(query.toLowerCase()));
    
    // 这里可以创建下拉建议框
    console.log('搜索建议:', suggestions);
}

// 隐藏搜索建议
function hideSearchSuggestions() {
    // 隐藏建议框
}

// 显示搜索结果
function displaySearchResults(results) {
    console.log('搜索结果:', results);
    // 这里可以更新页面显示搜索结果
}

// 工具卡片交互
function initToolCards() {
    const toolCards = document.querySelectorAll('.tool-card');
    
    toolCards.forEach(card => {
        // 鼠标悬停效果
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        // 点击事件
        const primaryBtn = card.querySelector('.btn-primary');
        const secondaryBtn = card.querySelector('.btn-secondary');
        
        if (primaryBtn) {
            primaryBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const toolName = card.querySelector('h3').textContent;
                handleToolAction(toolName, 'use');
            });
        }
        
        if (secondaryBtn) {
            secondaryBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const toolName = card.querySelector('h3').textContent;
                handleToolAction(toolName, 'details');
            });
        }
    });
}

// 处理工具操作
function handleToolAction(toolName, action) {
    console.log(`${action} ${toolName}`);
    
    if (action === 'use') {
        // 跳转到工具官网或使用页面
        showNotification(`正在跳转到 ${toolName}...`);
    } else if (action === 'details') {
        // 显示工具详情
        showToolDetails(toolName);
    }
}

// 显示工具详情
function showToolDetails(toolName) {
    // 创建模态框显示工具详情
    const modal = createModal();
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>${toolName} 详细信息</h2>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <p>这里是 ${toolName} 的详细信息...</p>
                <div class="tool-features">
                    <h3>主要功能</h3>
                    <ul>
                        <li>功能1</li>
                        <li>功能2</li>
                        <li>功能3</li>
                    </ul>
                </div>
                <div class="tool-pricing">
                    <h3>价格信息</h3>
                    <p>免费版：基础功能</p>
                    <p>付费版：$20/月</p>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-primary">立即使用</button>
                <button class="btn-secondary modal-close">关闭</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 关闭模态框事件
    modal.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            document.body.removeChild(modal);
        });
    });
    
    // 点击背景关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// 创建模态框
function createModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    return modal;
}

// 滚动效果
function initScrollEffects() {
    // 导航栏滚动效果
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 100) {
            navbar.style.background = 'rgba(255,255,255,0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.background = '#fff';
            navbar.style.backdropFilter = 'none';
        }
    });
    
    // 元素进入视口动画
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // 观察所有卡片元素
    document.querySelectorAll('.category-card, .tool-card, .review-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

// 移动端菜单
function initMobileMenu() {
    // 如果需要汉堡菜单，可以在这里添加
    const navMenu = document.querySelector('.nav-menu');
    
    // 检测屏幕尺寸变化
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            navMenu.style.display = 'flex';
        }
    });
}

// 显示通知
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #6366f1;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 显示加载状态
function showLoadingState() {
    const loading = document.createElement('div');
    loading.id = 'loading-overlay';
    loading.innerHTML = `
        <div class="loading-content">
            <div class="loading"></div>
            <p>正在搜索...</p>
        </div>
    `;
    loading.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255,255,255,0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    `;
    
    document.body.appendChild(loading);
}

// 隐藏加载状态
function hideLoadingState() {
    const loading = document.getElementById('loading-overlay');
    if (loading) {
        document.body.removeChild(loading);
    }
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .modal .modal-content {
        background: white;
        border-radius: 16px;
        max-width: 600px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    .modal-header {
        padding: 20px;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .modal-body {
        padding: 20px;
    }
    
    .modal-footer {
        padding: 20px;
        border-top: 1px solid #e2e8f0;
        display: flex;
        gap: 10px;
        justify-content: flex-end;
    }
    
    .modal-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #64748b;
    }
    
    .loading-content {
        text-align: center;
    }
    
    .loading-content p {
        margin-top: 20px;
        color: #64748b;
        font-weight: 500;
    }
`;

document.head.appendChild(style);

// 工具数据（实际项目中应该从API获取）
const toolsData = {
    'ChatGPT': {
        name: 'ChatGPT',
        category: 'AI聊天助手',
        rating: 4.8,
        description: 'OpenAI开发的强大对话AI，支持文本生成、代码编写、问题解答等多种任务',
        features: ['自然语言对话', '代码生成', '文本创作', '问题解答', '多语言支持'],
        pricing: {
            free: '免费版：基础功能',
            paid: 'ChatGPT Plus：$20/月'
        },
        website: 'https://chat.openai.com'
    },
    'Claude': {
        name: 'Claude',
        category: 'AI聊天助手',
        rating: 4.7,
        description: 'Anthropic开发的安全可靠的AI助手，擅长长文本处理和复杂推理',
        features: ['长文本处理', '复杂推理', '安全对话', '文档分析', '创意写作'],
        pricing: {
            free: '免费版：基础功能',
            paid: 'Claude Pro：$20/月'
        },
        website: 'https://claude.ai'
    },
    'Midjourney': {
        name: 'Midjourney',
        category: 'AI图像生成',
        rating: 4.9,
        description: '顶级AI图像生成工具，通过Discord使用，生成高质量艺术作品',
        features: ['高质量图像生成', 'Discord集成', '多种艺术风格', '图像变体', '高分辨率输出'],
        pricing: {
            free: '免费试用：25张图片',
            paid: '基础版：$10/月，标准版：$30/月'
        },
        website: 'https://midjourney.com'
    }
};