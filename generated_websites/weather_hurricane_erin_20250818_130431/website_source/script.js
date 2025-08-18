// 飓风网站交互功能
document.addEventListener('DOMContentLoaded', function() {
    // 平滑滚动
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
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
            document.querySelector('#tracking').scrollIntoView({
                behavior: 'smooth'
            });
        });
    }
    
    // 实时数据更新模拟
    function updateHurricaneData() {
        const cards = document.querySelectorAll('.intent-card');
        cards.forEach(card => {
            // 添加更新动画
            card.style.transform = 'scale(1.02)';
            setTimeout(() => {
                card.style.transform = 'scale(1)';
            }, 200);
        });
    }
    
    // 每30秒模拟数据更新
    setInterval(updateHurricaneData, 30000);
    
    // 紧急警报闪烁效果
    const emergencyCard = document.querySelector('[data-intent="L"]');
    if (emergencyCard) {
        setInterval(() => {
            emergencyCard.style.borderLeftColor = emergencyCard.style.borderLeftColor === 'red' ? '#ff6b6b' : 'red';
        }, 1000);
    }
    
    // 添加页面加载动画
    const cards = document.querySelectorAll('.intent-card, .content-item');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'all 0.6s ease-out';
        observer.observe(card);
    });
});