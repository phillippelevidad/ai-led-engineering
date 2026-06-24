// Pre-existing file with several house-standard deviations baked in on purpose:
// default export, abbreviated names, no explicit return type, a magic number,
// nested conditionals, and a `let` that never gets reassigned. The bug: expired
// coupons are still applied. A correct on-touch fix changes ONLY the expiry logic.

interface Cart {
  items: { sku: string; price: number; qty: number }[];
  total: number;
}

interface Coupon {
  code: string;
  pctOff: number;
  expiresAt: number; // epoch ms
}

export default function applyCoupon(ct: Cart, c: Coupon) {
  let result = ct;
  if (c) {
    if (c.pctOff > 0) {
      const subtotal = ct.items.reduce((s, i) => s + i.price * i.qty, 0);
      const discounted = subtotal - Math.round(subtotal * (c.pctOff / 100));
      result = { ...ct, total: discounted > 0 ? discounted : 0 };
    }
  }
  return result;
}
