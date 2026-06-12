import React from "react";
import {
  Archive,
  Banknote,
  BriefcaseBusiness,
  Bus,
  Car,
  ChartNoAxesColumn,
  CircleHelp,
  Clapperboard,
  Dumbbell,
  Gift,
  GraduationCap,
  HandCoins,
  HeartPulse,
  Home,
  Landmark,
  PawPrint,
  Plane,
  ReceiptText,
  Shirt,
  ShoppingBasket,
  ShoppingCart,
  Tag,
  UtensilsCrossed,
  WalletCards,
  Wrench,
  type LucideIcon,
} from "lucide-react";

export type CategoryIconOption = {
  slug: string;
  label: string;
  keywords: string[];
  Icon: LucideIcon;
};

export const CATEGORY_ICON_OPTIONS: CategoryIconOption[] = [
  { slug: "receipt-text", label: "Recibo", keywords: ["factura", "ticket", "comprobante"], Icon: ReceiptText },
  { slug: "utensils-crossed", label: "Comida", keywords: ["alimentación", "restaurante", "cena"], Icon: UtensilsCrossed },
  { slug: "shopping-basket", label: "Supermercado", keywords: ["compras", "mercado", "canasta"], Icon: ShoppingBasket },
  { slug: "shopping-cart", label: "Compras", keywords: ["tienda", "carrito", "gastos"], Icon: ShoppingCart },
  { slug: "paw-print", label: "Mascotas", keywords: ["perro", "gato", "animales"], Icon: PawPrint },
  { slug: "archive", label: "Archivo", keywords: ["caja", "histórico"], Icon: Archive },
  { slug: "home", label: "Hogar", keywords: ["casa", "alquiler", "vivienda"], Icon: Home },
  { slug: "car", label: "Auto", keywords: ["vehículo", "nafta", "transporte"], Icon: Car },
  { slug: "bus", label: "Transporte", keywords: ["colectivo", "viaje", "movilidad"], Icon: Bus },
  { slug: "plane", label: "Viajes", keywords: ["vacaciones", "avión", "turismo"], Icon: Plane },
  { slug: "heart-pulse", label: "Salud", keywords: ["médico", "farmacia", "bienestar"], Icon: HeartPulse },
  { slug: "dumbbell", label: "Deporte", keywords: ["gimnasio", "fitness", "actividad"], Icon: Dumbbell },
  { slug: "clapperboard", label: "Entretenimiento", keywords: ["cine", "series", "salidas"], Icon: Clapperboard },
  { slug: "shirt", label: "Ropa", keywords: ["indumentaria", "vestimenta", "moda"], Icon: Shirt },
  { slug: "graduation-cap", label: "Educación", keywords: ["estudio", "cursos", "aprendizaje"], Icon: GraduationCap },
  { slug: "briefcase-business", label: "Trabajo", keywords: ["negocio", "oficina", "profesional"], Icon: BriefcaseBusiness },
  { slug: "gift", label: "Regalos", keywords: ["cumpleaños", "presente", "celebración"], Icon: Gift },
  { slug: "wrench", label: "Mantenimiento", keywords: ["arreglo", "reparación", "servicio"], Icon: Wrench },
  { slug: "banknote", label: "Efectivo", keywords: ["dinero", "billete", "cash"], Icon: Banknote },
  { slug: "wallet-cards", label: "Billetera", keywords: ["tarjeta", "cuenta", "pago"], Icon: WalletCards },
  { slug: "landmark", label: "Banco", keywords: ["finanzas", "institución", "ahorro"], Icon: Landmark },
  { slug: "hand-coins", label: "Ingresos", keywords: ["sueldo", "cobro", "ganancia"], Icon: HandCoins },
  { slug: "chart-no-axes-column", label: "Análisis", keywords: ["gráfico", "estadística", "balance"], Icon: ChartNoAxesColumn },
  { slug: "tag", label: "Etiqueta", keywords: ["categoría", "general", "otros"], Icon: Tag },
];

const CATEGORY_ICON_ALIASES: Record<string, string> = {
  briefcase: "briefcase-business",
  chart: "chart-no-axes-column",
  chartColumn: "chart-no-axes-column",
  shopping: "shopping-cart",
  utensils: "utensils-crossed",
};

export function normalizeCategoryIconSlug(icon: string): string {
  const trimmedIcon = icon.trim();

  return CATEGORY_ICON_ALIASES[trimmedIcon] ?? trimmedIcon;
}

export function getCategoryIconOption(icon: string): CategoryIconOption | null {
  const normalizedIcon = normalizeCategoryIconSlug(icon);

  return CATEGORY_ICON_OPTIONS.find((option) => option.slug === normalizedIcon) ?? null;
}

type CategoryIconProps = {
  icon: string;
  size?: number;
};

export function CategoryIcon({ icon, size = 18 }: CategoryIconProps) {
  const iconOption = getCategoryIconOption(icon);
  const Icon = iconOption?.Icon ?? CircleHelp;

  return <Icon aria-hidden="true" focusable="false" size={size} />;
}
