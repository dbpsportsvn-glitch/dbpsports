/**
 * Unified Cart Count Updater for Both Main Shop and Organization Shop
 * Cập nhật cart count trên tất cả trang shop
 */

function updateCartCount(newCount, shopType = 'main') {
    if (shopType === 'main') {
        // Update main shop cart count
        updateMainShopCartCount(newCount);
    } else if (shopType === 'organization') {
        // Update organization shop cart count
        updateOrganizationShopCartCount(newCount);
    }
}

function updateMainShopCartCount(newCount) {
    // Lưu cart count vào localStorage
    localStorage.setItem('main_cart_count', newCount);
    
    // Call the existing main cart count function
    if (typeof updateMainCartCount === 'function') {
        updateMainCartCount(newCount);
    }
    
    // Update cart count badge in main shop header
    const cartCountBadge = document.querySelector('.main-cart-count-badge');
    if (cartCountBadge) {
        cartCountBadge.textContent = newCount;
    }
    
    // Update cart count in main shop navigation
    const cartCountNav = document.querySelector('.main-cart-count-nav');
    if (cartCountNav) {
        cartCountNav.textContent = newCount;
    }
    
    // Update cart count in main shop buttons
    const cartCountBtn = document.querySelector('.main-cart-count-btn');
    if (cartCountBtn) {
        cartCountBtn.textContent = `Giỏ Hàng (${newCount})`;
    }
    
    // Show/hide cart count badge based on count
    if (newCount > 0) {
        if (cartCountBadge) {
            cartCountBadge.style.display = 'flex';
        }
        if (cartCountNav) {
            cartCountNav.style.display = 'inline';
        }
        if (cartCountBtn) {
            cartCountBtn.style.display = 'block';
        }
    } else {
        if (cartCountBadge) {
            cartCountBadge.style.display = 'none';
        }
        if (cartCountNav) {
            cartCountNav.style.display = 'none';
        }
        if (cartCountBtn) {
            cartCountBtn.style.display = 'none';
        }
    }
}

function updateOrganizationShopCartCount(newCount) {
    // Update cart count badge in header
    const cartCountBadge = document.querySelector('.cart-count-badge');
    if (cartCountBadge) {
        cartCountBadge.textContent = newCount;
    }
    
    // Update cart count in shop home button if exists
    const cartCountBtn = document.querySelector('.cart-count-btn span');
    if (cartCountBtn) {
        cartCountBtn.textContent = `Giỏ Hàng (${newCount})`;
    }
    
    // Update cart count in banner button if exists
    const bannerCartBtn = document.querySelector('.cart-count-btn');
    if (bannerCartBtn) {
        bannerCartBtn.textContent = newCount;
    }
    
    // Show/hide cart count badge based on count
    if (newCount > 0) {
        if (cartCountBadge) {
            cartCountBadge.style.display = 'flex';
        }
        if (cartCountBtn) {
            cartCountBtn.parentElement.style.display = 'block';
        }
        if (bannerCartBtn) {
            bannerCartBtn.style.display = 'block';
        }
    } else {
        if (cartCountBadge) {
            cartCountBadge.style.display = 'none';
        }
        if (cartCountBtn) {
            cartCountBtn.parentElement.style.display = 'none';
        }
        if (bannerCartBtn) {
            bannerCartBtn.style.display = 'none';
        }
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { updateCartCount, updateMainShopCartCount, updateOrganizationShopCartCount };
}
