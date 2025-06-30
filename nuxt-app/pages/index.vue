<script setup>
const baseURL = useRuntimeConfig().public.baseUrl;
const toast = useToast();
const token = ref("");
const itoken = ref("");
const ntoken = ref("");
const ctoken = ref("");
const file_url = ref("");
const download_url = ref("");
const is_ntoken_Copied = ref(false);
const is_ctoken_Copied = ref(false);
const is_url_Copied = ref(false);
const auth_items = ref(['subadmin', 'user']);
const auth_value = ref('user');
const expire = ref(3600);

function showError(msg) {
    toast.add({ title: msg, color: "error", duration: 3000 });
}

function saveToken(t) {
    if (t) {
        localStorage.setItem('token', t);
    }
    token.value = localStorage.getItem('token');
    itoken.value = token.value;
}

async function doRenew() {
    try {
        const data = await $fetch("/renew", {
            baseURL: baseURL,
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${token.value}`
            }
        });
        if (data.token) {
            ntoken.value = data.token;
            saveToken(ntoken.value);
        } else {
            showError(data.msg);
        }
    } catch (error) {
        showError("Failed to renew token.");
    }
}

async function doCreate() {
    try {
        const data = await $fetch("/create?auth=" + (auth_value.value === "user" ? 2 : 1) + "&expire=" + expire.value, {
            baseURL: baseURL,
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${token.value}`
            }
        });
        if (data.token) {
            ctoken.value = data.token;
        } else {
            showError(data.msg);
        }
    } catch (error) {
        showError("Failed to create token.");
    }
}

async function doInvalitate() {
    try {
        const data = await $fetch("/invalidate", {
            baseURL: baseURL,
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `${token.value}`
            }
        });
        if (data.msg === "ok") {
            localStorage.setItem('token', '');
            token.value = localStorage.getItem('token');
        } else {
            showError(data.msg);
        }
    } catch (error) {
        showError("Failed to invalidate token.");
    }
}

async function uploadFile() {
    const file = document.getElementById("file").files[0];
    const formData = new FormData();
    formData.append("file", file);
    try {
        const data = await $fetch("/upload", {
            baseURL: baseURL,
            method: "POST",
            headers: {
                "Authorization": `${token.value}`
            },
            body: formData
        });
        if (data.msg === "ok") {
            console.log("ok");
            file_url.value = data.filename;
            download_url.value = data.filename;
            document.getElementById("file").value = "";
        } else {
            showError(data.msg);
        }
    } catch (error) {
        showError("Failed to upload file.");
    }
}

async function downloadFile() {
    const realurl = baseURL + "/download/" + download_url.value;
    try {
        const response = await $fetch.raw(realurl, {
            baseURL: baseURL,
            method: "GET",
            headers: {
                "Authorization": `${token.value}`
            }
        });
        const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/octet-stream' }));
        const link = document.createElement('a');
        link.style.display = 'none';
        link.download = download_url.value;
        link.href = url;
        document.body.appendChild(link);
        link.click();
    } catch (error) {
        if (error.response?.status === 401 || error.response?.status === 404)
            showError(error.response._data.msg);
        else
            showError("Failed to download file.");
    }
}

async function copyRenewTokenToClipboard() {
    await navigator.clipboard.writeText(ntoken.value);
    is_ntoken_Copied.value = true;
    setTimeout(() => is_ntoken_Copied.value = false, 2000);
}

async function copyCreateTokenToClipboard() {
    await navigator.clipboard.writeText(ctoken.value);
    is_ctoken_Copied.value = true;
    setTimeout(() => is_ctoken_Copied.value = false, 2000);
}

async function copyUrl() {
    await navigator.clipboard.writeText(file_url.value);
    is_url_Copied.value = true;
    setTimeout(() => is_url_Copied.value = false, 2000);
}

onMounted(() => {
    token.value = localStorage.getItem('token');
    itoken.value = token.value;
})

</script>

<template>
    <div class="min-h-screen bg-gray-100">
        <div class="mx-auto pt-16 max-w-4xl">
            <UCard>
                <div class="space-y-3 px-4">
                    <div class="text-center text-3xl font-bold">Token File Server</div>
                    <div class="text-center text-sm text-gray-500">current token: {{ token }}</div>

                    <USeparator />
                    <div class="flex justify-center">
                        <UButtonGroup class="w-full">
                            <UBadge color="neutral" variant="outline" label="current" class="min-w-20 justify-center">
                            </UBadge>
                            <UInput color="neutral" variant="outline" placeholder="token" class="grow min-w-0"
                                v-model="token" disabled></UInput>
                        </UButtonGroup>
                        <UButton class="justify-center ml-2 min-w-30" @click="doInvalitate(token)">Invalidate</UButton>
                    </div>

                    <div class="flex justify-center">
                        <UButtonGroup class="w-full">
                            <UBadge color="neutral" variant="outline" label="token" class="min-w-20 justify-center">
                            </UBadge>
                            <UInput color="neutral" variant="outline" placeholder="token" class="grow min-w-0"
                                v-model="itoken"></UInput>
                        </UButtonGroup>
                        <UButton class="justify-center ml-2 min-w-30" @click="saveToken(itoken)">Set Token</UButton>
                    </div>
                    <div class="flex justify-center">
                        <UButtonGroup class="w-full">
                            <UBadge color="neutral" variant="outline" label="token" class="min-w-20 justify-center">
                            </UBadge>
                            <UInput color="neutral" variant="outline" placeholder="token" class="grow min-w-0" disabled
                                v-model="ntoken"></UInput>
                            <UButton color="neutral" variant="outline"
                                :icon="is_ntoken_Copied ? 'i-lucide-copy-check' : 'i-lucide-copy'"
                                @click="copyRenewTokenToClipboard()"></UButton>
                        </UButtonGroup>
                        <UButton class="justify-center ml-2 min-w-30" @click="doRenew()">Renew Token</UButton>
                    </div>
                    <div class="flex justify-center">
                        <UButtonGroup class="w-full">
                            <UBadge color="neutral" variant="outline" label="create" class="min-w-20 justify-center">
                            </UBadge>
                            <UInput color="neutral" variant="outline" placeholder="token" class="grow min-w-0" disabled
                                v-model="ctoken"></UInput>
                            <UButton color="neutral" variant="outline"
                                :icon="is_ctoken_Copied ? 'i-lucide-copy-check' : 'i-lucide-copy'"
                                @click="copyCreateTokenToClipboard()"></UButton>
                            <UBadge color="neutral" variant="outline" label="auth"></UBadge>
                            <USelect color="neutral" variant="outline" class="min-w-30" :items="auth_items"
                                v-model="auth_value"></USelect>
                            <UBadge color="neutral" variant="outline" label="expire"></UBadge>
                            <UInput color="neutral" variant="outline" placeholder="expire" class="max-w-20"
                                v-model="expire"></UInput>
                        </UButtonGroup>
                        <UButton class="justify-center ml-2 min-w-30" @click="doCreate()">Create Token</UButton>
                    </div>
                    <div class="flex justify-center">
                        <UButtonGroup class="w-full">
                            <UBadge color="neutral" variant="outline" label="upload" class="min-w-20 justify-center">
                            </UBadge>
                            <UInput id="file" type="file" color="neutral" variant="outline" class="max-w-50"></UInput>
                            <UBadge color="neutral" variant="outline" label="url" class="min-w-20 justify-center">
                            </UBadge>
                            <UInput color="neutral" variant="outline" placeholder="upload" class="grow min-w-0"
                                v-model="file_url" disabled></UInput>
                            <UButton color="neutral" variant="outline"
                                :icon="is_url_Copied ? 'i-lucide-copy-check' : 'i-lucide-copy'" @click="copyUrl()">
                            </UButton>
                        </UButtonGroup>
                        <UButton type="submit" class="justify-center ml-2 min-w-30" @click="uploadFile()">Upload
                        </UButton>
                    </div>
                    <div class="flex justify-center">
                        <UButtonGroup class="w-full">
                            <UBadge color="neutral" variant="outline" label="url" class="min-w-20 justify-center">
                            </UBadge>
                            <UInput color="neutral" variant="outline" class="grow" v-model="download_url"></UInput>
                        </UButtonGroup>
                        <UButton type="submit" class="justify-center ml-2 min-w-30" @click="downloadFile()">Download
                        </UButton>
                    </div>
                </div>
            </UCard>
            <div class="hidden">
                <UIcon name="i-lucide-copy"></UIcon>
                <UIcon name="i-lucide-copy-check"></UIcon>
            </div>
        </div>
    </div>
</template>