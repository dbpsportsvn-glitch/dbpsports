-- Update e-wallet payment method name with Vietnamese accents
UPDATE shop_paymentmethod 
SET name = 'Ví điện tử',
    description = 'Thanh toán qua Momo, ZaloPay, VNPay'
WHERE payment_type = 'e_wallet';

-- Verify the update
SELECT id, name, payment_type, description FROM shop_paymentmethod WHERE payment_type = 'e_wallet';

