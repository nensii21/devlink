const DEVELOPER_QUOTES = [
  "Small improvements every day create remarkable software.",
  "Code is like humor. When you have to explain it, it’s bad.",
  "First, solve the problem. Then, write the code.",
  "The best error message is the one that never shows up.",
  "Simplicity is the soul of efficiency.",
  "Make it work, make it right, make it fast.",
  "Perfect is the enemy of good.",
  "Talk is cheap. Show me the code.",
  "Programs must be written for people to read, and only incidentally for machines to execute.",
  "Digital design is like painting, except the paint never dries."
];

export const getRandomQuote = () => {
  const index = Math.floor(Math.random() * DEVELOPER_QUOTES.length);
  return DEVELOPER_QUOTES[index];
};

export const getDailyQuote = () => {
  // Use day of the year to get a stable quote per day
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const diff = now.getTime() - start.getTime();
  const oneDay = 1000 * 60 * 60 * 24;
  const day = Math.floor(diff / oneDay);
  
  return DEVELOPER_QUOTES[day % DEVELOPER_QUOTES.length];
};
