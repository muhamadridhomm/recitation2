function observeImage(node) {
	if (imageObserver) {
		imageObserver.observe(node);
	}
	return {
		destroy() {
			if (imageObserver) {
				imageObserver.unobserve(node);
			}
		}
	};
}
