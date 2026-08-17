# Tencent OCR API reference

Provider facts in this skill are limited to the official Tencent contracts:

- [GeneralBasicOCR](https://cloud.tencent.com/document/api/866/33526): action,
  request fields, response fields, image limits, and text detections.
- [GeneralAccurateOCR](https://cloud.tencent.com/document/api/866/34937): bounded
  repair action only; it is excluded from the live probe.
- [OCR error codes](https://cloud.tencent.com/document/api/866/33528): provider
  error envelope and named error codes.
- [TC3-HMAC-SHA256 signing](https://intl.cloud.tencent.com/document/product/1079/63098):
  canonical request, credential scope, signing key, and Authorization header.
- [Common request parameters](https://cloud.tencent.com/document/product/1278/46716):
  `X-TC-Action`, `X-TC-Version`, `X-TC-Timestamp`, host, and authorization.

PaperGraph sends POST to `ocr.tencentcloudapi.com`, version `2018-11-19`, with
JSON `{"ImageBase64":"..."}`. The content type and host are canonical signed
headers. The serialized bytes used for the payload hash are the bytes transmitted.

For a local PDF, the official GeneralBasicOCR input contract additionally
requires `"IsPdf":true`; `PdfPageNumber` selects the single page and defaults to
1. PaperGraph always sends the page explicitly and bounds it to 1..10,000 as a
local fail-closed policy. The one-call live probe remains image-only because its
normalizer requires trustworthy local pixel dimensions.

The provider response is observation, not interpretation. `DetectedText`,
confidence, polygon, angle, language, and request ID may populate the normalized
source. Headings, claims, argument structure, and conclusions are PaperGraph
inferences and must never be represented as provider output.
