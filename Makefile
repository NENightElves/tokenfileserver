all:
	cd nuxt-app && npm install && npm run generate; \
	cd .. && rm -r static; \
	cp -r nuxt-app/.output/public static;
