module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      // SDK 54 + reanimated 4 → el plugin vive en react-native-worklets
      // y debe ir SIEMPRE al final de la lista.
      'react-native-worklets/plugin',
    ],
  };
};
