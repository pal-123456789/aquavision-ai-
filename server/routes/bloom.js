
const express = require('express');
const router = express.Router();
const bloomController = require('../controllers/bloomController');
const { protect } = require('../middleware/auth');
router.post('/detect', protect, bloomController.detect);
router.get('/nearby', bloomController.nearby);
router.get('/:id', bloomController.getById);
module.exports = router;
