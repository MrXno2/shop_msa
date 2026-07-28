export function calcDiscountedPrice(price: string, sale: string | null): number {
  const p = parseFloat(price)
  if (!sale) return p
  return p * (1 - parseFloat(sale) / 100)
}
