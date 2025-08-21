// Hurricane Erin 天气预警信息中心 - 主要JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initNavigation();
    initWeatherUpdates();
    initAlerts();
    initAnimations();
    initResponsiveFeatures();
});

// 导航功能
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // 高亮当前导航项
    window.addEventListener('scroll', highlightCurrentSection);
}

// 高亮当前区域的导航项
function highlightCurrentSection() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let currentSection = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        const sectionHeight = section.offsetHeight;
        
        if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
            currentSection = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + currentSection) {
            link.classList.add('active');
        }
    });
}

// 天气数据更新功能
function initWeatherUpdates() {
    // 模拟实时天气数据更新
    setInterval(updateWeatherData, 30000); // 每30秒更新一次
    
    // 初始加载天气数据
    updateWeatherData();
}

function updateWeatherData() {
    // 模拟天气数据
    const weatherData = {
        position: {
            lat: (25.5 + Math.random() * 0.1 - 0.05).toFixed(1),
            lng: (-80.2 + Math.random() * 0.1 - 0.05).toFixed(1)
        },
        windSpeed: (120 + Math.random() * 20 - 10).toFixed(0),
        pressure: (965 + Math.random() * 10 - 5).toFixed(0),
        direction: ['Northwest', 'North-Northwest', 'West-Northwest'][Math.floor(Math.random() * 3)],
        moveSpeed: (15 + Math.random() * 5 - 2.5).toFixed(0)
    };
    
    // 更新页面上的天气数据
    updateWeatherDisplay(weatherData);
}

function updateWeatherDisplay(data) {
    const weatherDetails = document.querySelector('.weather-details');
    if (weatherDetails) {
        weatherDetails.innerHTML = `
            <p><strong>纬度:</strong> ${data.position.lat}°N</p>
            <p><strong>经度:</strong> ${data.position.lng}°W</p>
            <p><strong>风速:</strong> ${data.windSpeed} km/h</p>
            <p><strong>气压:</strong> ${data.pressure} hPa</p>
        `;
    }
    
    const pathInfo = document.querySelector('.path-info');
    if (pathInfo) {
        pathInfo.innerHTML = `
            <p>🧭 <strong>Direction:</strong> ${data.direction}</p>
            <p>⚡ <strong>Movement Speed:</strong> ${data.moveSpeed} km/h</p>
            <p>📍 <strong>Expected Landfall:</strong> ${calculateLandfall()} hours</p>
            <p>⚠️ <strong>Threat Level:</strong> Category ${getThreatLevel()} Hurricane</p>
        `;
    }
}

function calculateLandfall() {
    // 模拟计算登陆时间
    return (48 + Math.random() * 12 - 6).toFixed(0);
}

function getThreatLevel() {
    // 模拟威胁等级
    return Math.floor(Math.random() * 2) + 3; // 3-4级
}

// 警报系统
function initAlerts() {
    // 检查是否需要显示紧急警报
    checkEmergencyAlerts();
    
    // 每5分钟检查一次警报
    setInterval(checkEmergencyAlerts, 300000);
}

function checkEmergencyAlerts() {
    // Simulate alert checking logic
    const alertLevel = Math.random();
    
    if (alertLevel > 0.7) {
        showAlert('High Alert', 'Hurricane Erin intensity strengthening, take protective measures immediately!', 'danger');
    } else if (alertLevel > 0.4) {
        showAlert('Medium Alert', 'Hurricane Erin path may change, monitor closely.', 'warning');
    }
}

function showAlert(title, message, type) {
    // 创建警报元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <div class="alert-content">
            <strong>${title}:</strong> ${message}
            <button class="alert-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // 添加到页面顶部
    document.body.insertBefore(alertDiv, document.body.firstChild);
    
    // 5秒后自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// 动画效果
function initAnimations() {
    // 观察器用于触发滚动动画
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, {
        threshold: 0.1
    });
    
    // 观察所有卡片元素
    document.querySelectorAll('.tracking-card, .safety-card, .forecast-day').forEach(card => {
        observer.observe(card);
    });
    
    // 添加悬停效果
    addHoverEffects();
}

function addHoverEffects() {
    // 为卡片添加悬停效果
    document.querySelectorAll('.tracking-card, .safety-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// 响应式功能
function initResponsiveFeatures() {
    // 移动端菜单切换
    const navToggle = document.createElement('button');
    navToggle.className = 'nav-toggle';
    navToggle.innerHTML = '☰';
    navToggle.style.display = 'none';
    
    const navContainer = document.querySelector('.nav-container');
    if (navContainer) {
        navContainer.appendChild(navToggle);
    }
    
    navToggle.addEventListener('click', toggleMobileMenu);
    
    // 监听窗口大小变化
    window.addEventListener('resize', handleResize);
    handleResize(); // 初始调用
}

function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('mobile-active');
    }
}

function handleResize() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (window.innerWidth <= 768) {
        if (navToggle) navToggle.style.display = 'block';
        if (navMenu) navMenu.classList.add('mobile-menu');
    } else {
        if (navToggle) navToggle.style.display = 'none';
        if (navMenu) {
            navMenu.classList.remove('mobile-menu', 'mobile-active');
        }
    }
}

// 工具函数
function formatTime(timestamp) {
    return new Date(timestamp).toLocaleString('zh-CN');
}

function formatDistance(meters) {
    if (meters < 1000) {
        return meters + ' meters';
    } else {
        return (meters / 1000).toFixed(1) + ' km';
    }
}

function formatSpeed(kmh) {
    return kmh + ' km/h (' + (kmh * 0.621371).toFixed(1) + ' mph)';
}

// 数据导出功能
function exportWeatherData() {
    const data = {
        timestamp: new Date().toISOString(),
        hurricane: 'Erin',
        position: document.querySelector('.weather-details').textContent,
        forecast: Array.from(document.querySelectorAll('.forecast-day')).map(day => ({
            day: day.querySelector('.day-name').textContent,
            temp: day.querySelector('.temp').textContent,
            condition: day.querySelector('.condition').textContent
        }))
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hurricane-erin-data-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// 分享功能
function shareWeatherInfo() {
    if (navigator.share) {
        navigator.share({
            title: 'Hurricane Erin 实时追踪',
            text: '查看Hurricane Erin的最新追踪信息和安全指南',
            url: window.location.href
        });
    } else {
        // 备用分享方式
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            showAlert('Share', 'Link copied to clipboard', 'success');
        });
    }
}

// 添加键盘快捷键支持
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S: 导出数据
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        exportWeatherData();
    }
    
    // Ctrl/Cmd + Shift + S: 分享
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        shareWeatherInfo();
    }
    
    // ESC: 关闭所有警报
    if (e.key === 'Escape') {
        document.querySelectorAll('.alert').forEach(alert => alert.remove());
    }
});

// 性能监控
function trackPerformance() {
    if ('performance' in window) {
        window.addEventListener('load', () => {
            const perfData = performance.getEntriesByType('navigation')[0];
            console.log('Page load time:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
        });
    }
}

// 错误处理
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    // Error reporting logic can be added here
});

// 初始化性能监控
trackPerformance();

// 添加CSS动画类
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        animation: slideInUp 0.6s ease-out;
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .alert {
        position: fixed;
        top: 90px;
        right: 20px;
        max-width: 400px;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1001;
        animation: slideInRight 0.3s ease-out;
    }
    
    .alert-danger {
        background: #ff6b6b;
        color: white;
    }
    
    .alert-warning {
        background: #ffa726;
        color: white;
    }
    
    .alert-success {
        background: #4caf50;
        color: white;
    }
    
    .alert-close {
        background: none;
        border: none;
        color: inherit;
        font-size: 20px;
        float: right;
        cursor: pointer;
        margin-left: 10px;
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .mobile-menu {
        display: none;
    }
    
    .mobile-menu.mobile-active {
        display: flex;
        flex-direction: column;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #1e3c72;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .nav-toggle {
        background: none;
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0.5rem;
    }
    
    @media (max-width: 768px) {
        .nav-menu {
            display: none;
        }
        
        .nav-toggle {
            display: block !important;
        }
    }
`;

document.head.appendChild(style);