/**
 * Carousel — paginado horizontal con dots y auto-rotación opcional.
 * Equivalente al `hero-swiper` del web, pero con gestos nativos.
 *
 *   <Carousel data={items} renderItem={(item) => <Slide ...>} autoPlay />
 */
import { useEffect, useRef, useState } from 'react';
import {
  Animated, Dimensions, FlatList, Pressable, StyleSheet, View,
  type NativeScrollEvent, type NativeSyntheticEvent, type ViewStyle,
} from 'react-native';

import { colors, radius, spacing } from '@/theme/tokens';

type Props<T> = {
  data: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  itemHeight?: number;
  autoPlay?: boolean;
  autoPlayInterval?: number;
  showDots?: boolean;
  style?: ViewStyle;
  /** Margen lateral entre slides; el ancho efectivo de cada slide se calcula. */
  gap?: number;
};

export function Carousel<T>({
  data, renderItem,
  itemHeight = 220,
  autoPlay = true,
  autoPlayInterval = 4500,
  showDots = true,
  style,
  gap = 12,
}: Props<T>) {
  const screenWidth = Dimensions.get('window').width;
  const itemWidth = screenWidth - spacing.xl * 2;
  const snapInterval = itemWidth + gap;

  const listRef = useRef<FlatList<T>>(null);
  const [index, setIndex] = useState(0);
  const userScrolling = useRef(false);

  // Auto-rotación cuando el usuario no está tocando
  useEffect(() => {
    if (!autoPlay || data.length < 2) return;
    const timer = setInterval(() => {
      if (userScrolling.current) return;
      const next = (index + 1) % data.length;
      listRef.current?.scrollToOffset({ offset: next * snapInterval, animated: true });
      setIndex(next);
    }, autoPlayInterval);
    return () => clearInterval(timer);
  }, [index, data.length, autoPlay, autoPlayInterval, snapInterval]);

  function onMomentumScrollEnd(e: NativeSyntheticEvent<NativeScrollEvent>) {
    const offset = e.nativeEvent.contentOffset.x;
    const i = Math.round(offset / snapInterval);
    setIndex(Math.max(0, Math.min(data.length - 1, i)));
    userScrolling.current = false;
  }

  function goTo(i: number) {
    setIndex(i);
    listRef.current?.scrollToOffset({ offset: i * snapInterval, animated: true });
  }

  return (
    <View style={style}>
      <FlatList
        ref={listRef}
        data={data}
        keyExtractor={(_, i) => String(i)}
        horizontal
        showsHorizontalScrollIndicator={false}
        decelerationRate="fast"
        snapToInterval={snapInterval}
        snapToAlignment="start"
        contentContainerStyle={{ paddingHorizontal: spacing.xl }}
        ItemSeparatorComponent={() => <View style={{ width: gap }} />}
        renderItem={({ item, index: i }) => (
          <View style={{ width: itemWidth, height: itemHeight }}>
            {renderItem(item, i)}
          </View>
        )}
        onScrollBeginDrag={() => { userScrolling.current = true; }}
        onMomentumScrollEnd={onMomentumScrollEnd}
      />

      {showDots && data.length > 1 ? (
        <View style={styles.dots}>
          {data.map((_, i) => (
            <Dot key={i} active={i === index} onPress={() => goTo(i)} />
          ))}
        </View>
      ) : null}
    </View>
  );
}

function Dot({ active, onPress }: { active: boolean; onPress: () => void }) {
  const w = useRef(new Animated.Value(active ? 24 : 8)).current;
  useEffect(() => {
    Animated.spring(w, {
      toValue: active ? 24 : 8, useNativeDriver: false, speed: 20, bounciness: 6,
    }).start();
  }, [active]);

  return (
    <Pressable onPress={onPress} hitSlop={8}>
      <Animated.View style={[
        styles.dot,
        { width: w, backgroundColor: active ? colors.brand : 'rgba(148,163,184,0.45)' },
      ]} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  dots: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: spacing.base,
  },
  dot: { height: 8, borderRadius: radius.full },
});
