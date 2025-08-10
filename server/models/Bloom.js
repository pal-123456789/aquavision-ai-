
const mongoose = require('mongoose');
const bloomSchema = new mongoose.Schema({
  location: { type: { type: String, default: 'Point' }, coordinates: { type: [Number], required: true } },
  severity: { type: Number, required: true },
  chlorophyll: { type: Number },
  temperature: { type: Number },
  detectedAt: { type: Date, default: Date.now },
  source: { type: String },
  meta: { type: Object },
}, { timestamps: true });
bloomSchema.index({ location: '2dsphere' });
module.exports = mongoose.model('Bloom', bloomSchema);
