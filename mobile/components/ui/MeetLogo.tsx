/**
 * MeetLogo — logo oficial de Google Meet (multicolor, estilo Material).
 * Convertido desde el SVG del producto (8 paths con colores Material Design).
 */
import Svg, { Path, Polygon, Rect } from 'react-native-svg';

export function MeetLogo({ size = 22 }: { size?: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 48 48">
      {/* Frame blanco central */}
      <Rect
        width={16}
        height={16}
        x={12}
        y={16}
        fill="#FFFFFF"
        transform="rotate(-90 20 24)"
      />
      {/* Hexágono azul (cuerpo izquierdo) */}
      <Polygon fill="#1E88E5" points="3,17 3,31 8,32 13,31 13,17 8,16" />
      {/* Verde inferior (cuerpo derecho-bajo) */}
      <Path
        fill="#4CAF50"
        d="M37,24v14c0,1.657-1.343,3-3,3H13l-1-5l1-5h14v-7l5-1L37,24z"
      />
      {/* Amarillo superior (cuerpo derecho-alto) */}
      <Path
        fill="#FBC02D"
        d="M37,10v14H27v-7H13l-1-5l1-5h21C35.657,7,37,8.343,37,10z"
      />
      {/* Azul oscuro inferior izquierdo */}
      <Path
        fill="#1565C0"
        d="M13,31v10H6c-1.657,0-3-1.343-3-3v-7H13z"
      />
      {/* Triángulo rojo superior izquierdo */}
      <Polygon fill="#E53935" points="13,7 13,17 3,17" />
      {/* Cuña verde oscuro (interior lente) */}
      <Polygon fill="#2E7D32" points="38,24 37,32.45 27,24 37,15.55" />
      {/* Cuña verde claro (lente exterior) */}
      <Path
        fill="#4CAF50"
        d="M46,10.11v27.78c0,0.84-0.98,1.31-1.63,0.78L37,32.45v-16.9l7.37-6.22C45.02,8.8,46,9.27,46,10.11z"
      />
    </Svg>
  );
}
