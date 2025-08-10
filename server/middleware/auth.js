
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req,res,next)).catch(next);
const protect = asyncHandler(async (req,res,next) => {
  let token = null;
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) token = authHeader.split(' ')[1];
  if (!token) return res.status(401).json({ message: 'Not authorized, token missing' });
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = await User.findById(decoded.id).select('-password');
    if (!req.user) return res.status(401).json({ message: 'User not found' });
    next();
  } catch (err) {
    return res.status(401).json({ message: 'Not authorized, token invalid' });
  }
});
module.exports = { protect, asyncHandler };
