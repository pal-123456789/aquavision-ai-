
const axios = require('axios');
const Bloom = require('../models/Bloom');
const logger = require('../utils/logger');

exports.detect = async (req,res,next) => {
  try {
    const { lat, lng } = req.body;
    if (typeof lat !== 'number' || typeof lng !== 'number') return res.status(400).json({ message: 'Invalid location' });
    const weatherPromise = axios.get(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&hourly=sea_surface_temperature`);
    const mlUrl = `${process.env.ML_SERVICE_URL.replace(/\/$/,'')}/predict`;
    const [weatherResp] = await Promise.all([weatherPromise]);
    const temperature = Array.isArray(weatherResp.data.hourly?.sea_surface_temperature) ? weatherResp.data.hourly.sea_surface_temperature[0] : null;
    const mlResp = await axios.post(mlUrl, { lat, lng, temperature });
    const { probability = 0, chlorophyll } = mlResp.data || {};
    const severity = Math.round(Math.min(100, probability*100));
    const bloom = await Bloom.create({
      location: { type: 'Point', coordinates: [lng, lat] },
      severity, chlorophyll, temperature, source: 'ml_pipeline', meta: { ml: mlResp.data },
    });
    res.status(201).json({ bloom });
  } catch (err) {
    logger.error('Detect error: %o', err.toString());
    next(err);
  }
};

exports.nearby = async (req,res,next) => {
  try {
    const lat = parseFloat(req.query.lat);
    const lng = parseFloat(req.query.lng);
    const radius = parseInt(req.query.radius || '5000', 10);
    if (Number.isNaN(lat) || Number.isNaN(lng)) return res.status(400).json({ message: 'Invalid lat/lng' });
    const blooms = await Bloom.find({
      location: { $nearSphere: { $geometry: { type: 'Point', coordinates: [lng, lat] }, $maxDistance: radius } },
    }).limit(200);
    res.json({ count: blooms.length, blooms });
  } catch (err) { next(err); }
};

exports.getById = async (req,res,next) => {
  try {
    const bloom = await Bloom.findById(req.params.id);
    if (!bloom) return res.status(404).json({ message: 'Not found' });
    res.json({ bloom });
  } catch (err) { next(err); }
};
