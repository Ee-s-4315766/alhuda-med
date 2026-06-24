import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { booking } = await req.json()

    const officePhone  = Deno.env.get('OFFICE_PHONE')       ?? '966501234567'
    const token        = Deno.env.get('ULTRAMSG_TOKEN')
    const instanceId   = Deno.env.get('ULTRAMSG_INSTANCE')

    // Message to office owner
    const officeMsg = `
🚗 *حجز جديد — مكتب موكار*

👤 العميل: ${booking.customer_name}
📞 الجوال: ${booking.customer_phone}
🚙 السيارة: ${booking.car_name}
📅 الاستلام: ${booking.pickup_date}
📅 التسليم: ${booking.dropoff_date}
⏱️ المدة: ${booking.days} يوم
💰 الإجمالي: *${booking.total} ر.س*
🆔 رقم الحجز: ${String(booking.id).slice(0, 8).toUpperCase()}
    `.trim()

    // Confirmation message to customer
    const customerMsg = `
✅ *تم تأكيد حجزك — مكتب موكار*

مرحباً ${booking.customer_name}،
شكراً لاختيارك مكتب موكار لتأجير السيارات 🌟

🚙 السيارة: ${booking.car_name}
📅 الاستلام: ${booking.pickup_date}
📅 التسليم: ${booking.dropoff_date}
⏱️ المدة: ${booking.days} يوم
💰 الإجمالي: *${booking.total} ر.س*

سيتواصل معك فريقنا قريباً لتأكيد موعد الاستلام.
📞 للاستفسار: 0501234567
    `.trim()

    if (token && instanceId) {
      await Promise.all([
        sendUltraMsg(instanceId, token, officePhone, officeMsg),
        sendUltraMsg(instanceId, token, booking.customer_phone, customerMsg),
      ])
      console.log('WhatsApp messages sent successfully')
    } else {
      // Log when not configured (for testing)
      console.log('WhatsApp not configured — would send:')
      console.log('Office:', officeMsg)
      console.log('Customer:', customerMsg)
    }

    return new Response(
      JSON.stringify({ success: true }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (err) {
    console.error('Error:', err)
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function sendUltraMsg(instanceId: string, token: string, to: string, body: string) {
  // Normalize Saudi number: 05xxxxxxxx → 96605xxxxxxxx
  const phone = to.startsWith('0') ? '966' + to.slice(1) : to

  const res = await fetch(`https://api.ultramsg.com/${instanceId}/messages/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ token, to: phone, body }),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(`UltraMsg error: ${JSON.stringify(data)}`)
  return data
}
