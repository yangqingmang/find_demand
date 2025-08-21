// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('基于搜索意图的内容平台已加载');
    
    // 平滑滚动到锚点
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // CTA按钮点击事件
    const ctaButton = document.querySelector('.cta-button');
    if (ctaButton) {
        ctaButton.addEventListener('click', function() {
            document.getElementById('intents').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        });
    }
    
    // 意图卡片悬停效果
    const intentCards = document.querySelectorAll('.intent-card');
    intentCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // 滚动时的导航栏效果
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 100) {
            navbar.style.background = 'rgba(102, 126, 234, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            navbar.style.backdropFilter = 'none';
        }
    });
    
    // 内容项目的渐入动画
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
    
    // 观察所有内容项目
    const contentItems = document.querySelectorAll('.content-item');
    contentItems.forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(30px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(item);
    });
    
    // 搜索意图统计
    const intentStats = {
        'I': '信息获取',
        'N': '导航直达', 
        'C': '商业评估',
        'E': '交易购买',
        'B': '行为后续',
        'L': '本地/到店'
    };
    
    console.log('网站包含的搜索意图类型:', intentStats);
    
    // 模拟数据加载
    function simulateDataLoading() {
        const loadingElements = document.querySelectorAll('.loading');
        loadingElements.forEach(element => {
            setTimeout(() => {
                element.style.display = 'none';
            }, 2000);
        });
    }
    
    simulateDataLoading();
});

// 工具函数：获取意图颜色
function getIntentColor(intent) {
    const colors = {
        'I': '#4CAF50',
        'N': '#2196F3',
        'C': '#FF9800',
        'E': '#F44336',
        'B': '#9C27B0',
        'L': '#607D8B'
    };
    return colors[intent] || '#667eea';
}

// 工具函数：格式化意图名称
function formatIntentName(intent) {
    const names = {
        'I': '信息获取',
        'N': '导航直达',
        'C': '商业评估', 
        'E': '交易购买',
        'B': '行为后续',
        'L': '本地/到店'
    };
    return names[intent] || '未知意图';
}

// 导出工具函数供其他脚本使用
window.IntentUtils = {
    getIntentColor,
    formatIntentName
};