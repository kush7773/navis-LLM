
const voices = window.speechSynthesis.getVoices();
console.log(voices.filter(v => v.lang.includes("en-IN")).map(v => v.name));

