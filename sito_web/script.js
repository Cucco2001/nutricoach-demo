// Variabili globali
const STREAMLIT_URL = "https://nutricoach.streamlit.app/"; // Inserisci qui l'URL della tua app Streamlit

// Gestione smooth scroll per i link di navigazione
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll per i link di navigazione
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

    // Effetto navbar on scroll
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 100) {
            navbar.style.background = 'rgba(255, 255, 255, 0.98)';
            navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.boxShadow = 'none';
        }
    });

    // Animazioni on scroll
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

    // Applica animazioni agli elementi
    const animatedElements = document.querySelectorAll('.pricing-card, .step, .benefit-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Funzione per mostrare il modal email
function showEmailForm() {
    const modal = document.getElementById('emailModal');
    modal.style.display = 'block';
    
    // Focus sull'input email
    setTimeout(() => {
        document.getElementById('userEmail').focus();
    }, 100);
}

// Funzione per nascondere il modal email
function hideEmailForm() {
    const modal = document.getElementById('emailModal');
    modal.style.display = 'none';
}

// Gestione submit form email
function handleEmailSubmit(event) {
    event.preventDefault();
    
    const email = document.getElementById('userEmail').value;
    
    if (!email || !isValidEmail(email)) {
        showNotification('Per favore inserisci un\'email valida', 'error');
        return;
    }

    // Salva l'email nel localStorage per eventuale uso futuro
    localStorage.setItem('nutricoach_beta_email', email);
    
    // Mostra messaggio di successo
    showNotification('Perfetto! Ti stiamo reindirizzando all\'app...', 'success');
    
    // Reindirizza dopo 2 secondi
    setTimeout(() => {
        window.open(STREAMLIT_URL, '_blank');
        hideEmailForm();
    }, 2000);
}

// Gestione submit newsletter
function handleNewsletterSubmit(event) {
    event.preventDefault();
    
    const email = event.target.querySelector('input[type="email"]').value;
    
    if (!email || !isValidEmail(email)) {
        showNotification('Per favore inserisci un\'email valida', 'error');
        return;
    }

    // Simula iscrizione newsletter
    showNotification('Grazie! Ti sei iscritto alla newsletter con successo!', 'success');
    event.target.reset();
    
    // In un'implementazione reale, qui invieresti l'email al tuo servizio di newsletter
    console.log('Newsletter signup:', email);
}

// Validazione email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Sistema di notifiche
function showNotification(message, type = 'info') {
    // Rimuovi notifiche esistenti
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());
    
    // Crea nuova notifica
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">
                ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
            </span>
            <span class="notification-message">${message}</span>
        </div>
    `;
    
    // Stili per la notifica
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
        color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 3000;
        transform: translateX(400px);
        transition: transform 0.3s ease;
        max-width: 300px;
        border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'error' ? '#f5c6cb' : '#bee5eb'};
    `;
    
    document.body.appendChild(notification);
    
    // Animazione di entrata
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Rimozione automatica dopo 4 secondi
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 4000);
}

// Chiudi modal cliccando fuori
window.addEventListener('click', function(event) {
    const modal = document.getElementById('emailModal');
    if (event.target === modal) {
        hideEmailForm();
    }
});

// Chiudi modal con ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideEmailForm();
    }
});

// Effetti parallax leggeri per l'hero
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero');
    const rate = scrolled * -0.5;
    
    if (hero) {
        hero.style.transform = `translateY(${rate}px)`;
    }
});

// Contatore animato per le statistiche
function animateCounter(element, start, end, duration) {
    let current = start;
    const range = end - start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    
    const timer = setInterval(() => {
        current += increment;
        element.textContent = current;
        
        if (current === end) {
            clearInterval(timer);
        }
    }, stepTime);
}

// Avvia animazioni contatori quando sono visibili
const statsObserver = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                const finalValue = stat.textContent;
                stat.textContent = '0';
                
                if (finalValue === '20') {
                    animateCounter(stat, 0, 20, 1000);
                } else if (finalValue === '100%') {
                    stat.textContent = '0%';
                    let current = 0;
                    const timer = setInterval(() => {
                        current += 2;
                        stat.textContent = current + '%';
                        if (current >= 100) {
                            clearInterval(timer);
                        }
                    }, 20);
                } else if (finalValue === '24/7') {
                    stat.textContent = '24/7';
                }
            });
            
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

document.addEventListener('DOMContentLoaded', function() {
    const heroStats = document.querySelector('.hero-stats');
    if (heroStats) {
        statsObserver.observe(heroStats);
    }
});

// Gestione responsive del menu (per implementazioni future)
function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    navMenu.classList.toggle('active');
}

// Debug info
console.log('NutriCoach Landing Page loaded successfully!');
console.log('Streamlit URL:', STREAMLIT_URL); 