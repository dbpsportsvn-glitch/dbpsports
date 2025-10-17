/**
 * Organization Shop Cart Count Updater
 * Cập nhật cart count trên tất cả trang organization shop
 */

function updateCartCount(newCount) {
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

// Export function for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { updateCartCount };
}
