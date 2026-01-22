/* global module */
module.exports = {
  presets: [["@babel/preset-env", { targets: { node: "current" } }]],
  transform: { "^.+\\.(ts|tsx)$": "ts-jest" }
};
