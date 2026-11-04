<script setup lang="ts">
import { ShieldCheck, UserPlus, Users } from '@lucide/vue'
import type { Farm, FarmInvitation, FarmMembership, FarmMembershipAudit, Paginated } from '~/types/api'

const { request, selectedFarmId } = useApi()
const members = ref<FarmMembership[]>([]); const invitations = ref<FarmInvitation[]>([]); const audits = ref<FarmMembershipAudit[]>([]); const farms = ref<Farm[]>([])
const loading = ref(true); const submitting = ref(false); const errorMessage = ref(''); const successMessage = ref('')
const form = reactive({ email: '', role: 'worker' as FarmMembership['role'] })
const currentFarm = computed(() => farms.value.find(item => item.id === selectedFarmId.value))
const availableRoles = computed(() => currentFarm.value?.role === 'owner' ? ['owner', 'manager', 'worker', 'viewer'] : ['worker', 'viewer'])

async function load() {
  if (!selectedFarmId.value) return
  loading.value = true; errorMessage.value = ''
  try {
    const [m, i, a, f] = await Promise.all([request<FarmMembership[]>('/farms/team/members/'), request<FarmInvitation[]>('/farms/team/invitations/'), request<FarmMembershipAudit[]>('/farms/team/audit/'), request<Paginated<Farm>>('/farms/')])
    members.value = m; invitations.value = i; audits.value = a; farms.value = f.results
  } catch { errorMessage.value = 'Only farm owners and managers can manage the team.' }
  finally { loading.value = false }
}
onMounted(load); watch(selectedFarmId, load)
async function invite() {
  submitting.value = true; errorMessage.value = ''; successMessage.value = ''
  try { await request<FarmInvitation>('/farms/team/invitations/', { method: 'POST', body: form }); form.email = ''; await load(); successMessage.value = 'Invitation queued for delivery.' }
  catch (error) { errorMessage.value = isRateLimitError(error) ? 'Too many invitation requests. Wait before trying again.' : 'The invitation could not be created. Check the email and role.' }
  finally { submitting.value = false }
}
async function updateMember(member: FarmMembership, changes: Record<string, unknown>) {
  errorMessage.value = ''; successMessage.value = ''
  try { await request<FarmMembership>(`/farms/team/members/${member.id}/`, { method: 'PATCH', body: changes }); await load(); successMessage.value = 'Membership updated.' }
  catch { errorMessage.value = 'The membership could not be updated. At least one active owner is required.' }
}
async function revokeInvitation(invitation: FarmInvitation) {
  errorMessage.value = ''; successMessage.value = ''
  try { await request(`/farms/team/invitations/${invitation.id}/`, { method: 'DELETE' }); await load(); successMessage.value = 'Invitation revoked.' }
  catch { errorMessage.value = 'The invitation could not be revoked.' }
}
</script>

<template><section><div class="page-heading"><div><p class="eyebrow">Farm settings</p><h1>Team and permissions</h1><p>Invite people, assign responsibilities, and review access changes.</p></div></div><p v-if="successMessage" class="success">{{ successMessage }}</p><p v-if="errorMessage" class="error">{{ errorMessage }}</p><div v-if="loading" class="grid gap-4"><Skeleton class="h-40" /><Skeleton class="h-40" /></div><template v-else-if="currentFarm"><div class="grid gap-6 xl:grid-cols-[1.5fr_1fr]"><Card><CardHeader><CardTitle class="flex items-center gap-2"><Users /> Active and inactive members</CardTitle><CardDescription>Owners control privileged roles; managers can manage workers and viewers.</CardDescription></CardHeader><CardContent><div v-for="member in members" :key="member.id" class="grid gap-3 border-b py-4 sm:grid-cols-[1fr_10rem_auto] sm:items-center"><div><strong class="block">{{ member.name }}</strong><small class="text-muted-foreground">{{ member.email || 'No email set' }}</small></div><select :value="member.role" :disabled="currentFarm.role !== 'owner' && ['owner','manager'].includes(member.role)" @change="updateMember(member, { role: ($event.target as HTMLSelectElement).value })"><option v-for="role in (currentFarm.role === 'owner' ? ['owner','manager','worker','viewer'] : ['worker','viewer'])" :key="role" :value="role">{{ role }}</option></select><Button variant="outline" size="sm" @click="updateMember(member, { is_active: !member.is_active })">{{ member.is_active ? 'Deactivate' : 'Reactivate' }}</Button></div></CardContent></Card><Card><CardHeader><CardTitle class="flex items-center gap-2"><UserPlus /> Invite member</CardTitle><CardDescription>Invitations expire after seven days and must be accepted using this email.</CardDescription></CardHeader><CardContent><form class="stack" @submit.prevent="invite"><label>Email <input v-model="form.email" type="email" required></label><label>Role <select v-model="form.role"><option v-for="role in availableRoles" :key="role" :value="role">{{ role }}</option></select></label><Button type="submit" :disabled="submitting">{{ submitting ? 'Sending…' : 'Send invitation' }}</Button></form></CardContent></Card></div><div class="mt-6 grid gap-6 xl:grid-cols-2"><Card><CardHeader><CardTitle>Invitations</CardTitle></CardHeader><CardContent><div v-for="item in invitations" :key="item.id" class="flex items-center justify-between gap-3 border-b py-3"><span><strong class="block">{{ item.email }}</strong><small>{{ item.role }} · expires {{ new Date(item.expires_at).toLocaleDateString() }}</small></span><span class="flex items-center gap-2"><Badge :variant="item.status === 'pending' && !item.is_expired ? 'secondary' : 'outline'">{{ item.is_expired ? 'expired' : item.status }}</Badge><Button v-if="item.status === 'pending'" variant="ghost" size="sm" @click="revokeInvitation(item)">Revoke</Button></span></div><p v-if="!invitations.length" class="empty-row">No invitations.</p></CardContent></Card><Card><CardHeader><CardTitle class="flex items-center gap-2"><ShieldCheck /> Access audit</CardTitle></CardHeader><CardContent><div v-for="item in audits" :key="item.id" class="border-b py-3"><strong class="block">{{ item.event_type.replaceAll('_', ' ') }} · {{ item.subject_email }}</strong><small>{{ item.from_role || 'none' }} → {{ item.to_role || 'none' }} · {{ item.actor_name }} · {{ new Date(item.created_at).toLocaleString() }}</small></div><p v-if="!audits.length" class="empty-row">No access changes recorded.</p></CardContent></Card></div></template></section></template>
