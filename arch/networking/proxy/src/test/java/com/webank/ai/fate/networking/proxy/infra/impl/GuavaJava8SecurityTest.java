/*
 * Copyright 2026 The FATE Authors. All Rights Reserved.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *     http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.webank.ai.fate.networking.proxy.infra.impl;

import com.google.common.cache.*;
import com.google.common.collect.MapMaker;
import com.google.common.util.concurrent.*;
import com.webank.ai.fate.api.core.BasicMeta;
import com.webank.ai.fate.api.networking.proxy.Proxy;
import com.webank.ai.fate.core.retry.*;
import com.webank.ai.fate.core.retry.factory.*;
import com.webank.ai.fate.core.retry.impl.attempt.operation.FixedTimeLimitAttemptOperation;
import io.grpc.*;
import io.grpc.protobuf.ProtoUtils;
import io.grpc.stub.ClientCalls;
import java.io.*;
import java.lang.reflect.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.Test;
import org.junit.experimental.runners.Enclosed;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Java 8 only: real project/library paths; finite, self-generated inert streams. */
@RunWith(Enclosed.class)
public class GuavaJava8SecurityTest {
    public static class ApiContracts {
        @Test public void actualRetryerKeepsSuccessPredicateAndStopContracts() throws Exception {
            AtomicInteger attempts=new AtomicInteger();
            Retryer<String> retry=RetryerBuilder.<String>newBuilder().retryIfResult(v -> "retry".equals(v))
                .withStopStrategy(StopStrategies.stopAfterMaxAttempt(3)).build();
            assertEquals("ok",retry.call(() -> attempts.incrementAndGet()<3?"retry":"ok"));
            assertEquals(3,attempts.get());
            Retryer<String> failure=RetryerBuilder.<String>newBuilder().retryIfAnyException()
                .withStopStrategy(StopStrategies.stopAfterMaxAttempt(2)).build();
            try { failure.call(() -> {throw new IOException("inert");}); fail("must stop"); }
            catch(RetryException expected){ assertEquals(2,expected.getNumberOfFailedAttempts()); assertTrue(expected.getCause() instanceof IOException); }
        }
        @Test public void actualTimeLimiterKeepsSuccessFailureAndCancellation() throws Exception {
            ExecutorService executor=Executors.newSingleThreadExecutor();
            try {
                FixedTimeLimitAttemptOperation<String> normal=new FixedTimeLimitAttemptOperation<>(SimpleTimeLimiter.create(executor),2,TimeUnit.SECONDS);
                assertEquals("ordinary",normal.call(() -> "ordinary"));
                try { normal.call(() -> {throw new IOException("inert");}); fail("must propagate failure"); }
                catch(ExecutionException expected){assertTrue(expected.getCause() instanceof IOException);}
                CountDownLatch blocked=new CountDownLatch(1),interrupted=new CountDownLatch(1);
                FixedTimeLimitAttemptOperation<String> timeout=new FixedTimeLimitAttemptOperation<>(SimpleTimeLimiter.create(executor),20,TimeUnit.MILLISECONDS);
                try { timeout.call(() -> {try {blocked.await();return "unreachable";}catch(InterruptedException expected){interrupted.countDown();throw expected;}});fail("must time out"); }
                catch(TimeoutException expected){assertTrue(interrupted.await(2,TimeUnit.SECONDS));}
            } finally { executor.shutdownNow();assertTrue(executor.awaitTermination(2,TimeUnit.SECONDS)); }
        }
        @Test public void realCacheAndFutureContractsMatchProjectUsage() throws Exception {
            List<RemovalCause> removals=new ArrayList<>();
            LoadingCache<String,String> cache=CacheBuilder.newBuilder().maximumSize(100)
                .expireAfterAccess(20,TimeUnit.MINUTES).weakValues().recordStats()
                .removalListener(n -> removals.add(n.getCause())).build(new CacheLoader<String,String>() {
                    @Override public String load(String key){return new String(key);}
                });
            String retained=cache.get("ordinary");assertSame(retained,cache.get("ordinary"));
            cache.invalidate("ordinary");cache.cleanUp();assertEquals(Arrays.asList(RemovalCause.EXPLICIT),removals);
            assertEquals(1,cache.stats().hitCount());assertEquals(1,cache.stats().loadSuccessCount());
            SettableFuture<String> future=SettableFuture.create();AtomicInteger listeners=new AtomicInteger();
            future.addListener(listeners::incrementAndGet,MoreExecutors.directExecutor());assertTrue(future.cancel(true));
            assertTrue(future.isCancelled());assertEquals(1,listeners.get());
        }
        @Test public void actualPipeKeepsFiniteByteStreamsChunkingAndClose() {
            byte[] payload="FATE-测试-payload".getBytes(StandardCharsets.UTF_8);AtomicInteger closes=new AtomicInteger();
            ByteArrayInputStream input=new ByteArrayInputStream(payload){@Override public void close(){closes.incrementAndGet();}};
            InputStreamToPacketUnidirectionalPipe pipe=new InputStreamToPacketUnidirectionalPipe(input,Proxy.Metadata.getDefaultInstance(),5);
            ByteArrayOutputStream output=new ByteArrayOutputStream();
            for(int i=0;i<8;i++){Proxy.Packet packet=pipe.read();if(packet==null)break;byte[] bytes=packet.getBody().getValue().toByteArray();assertTrue(bytes.length<=5);output.write(bytes,0,bytes.length);}
            assertArrayEquals(payload,output.toByteArray());assertNull(pipe.read());pipe.close();assertEquals(1,closes.get());assertTrue(pipe.isClosed());
        }
        @Test public void unchangedGrpc116FutureAndProjectProtobufWorkInMemory() throws Exception {
            BasicMeta.Endpoint endpoint=BasicMeta.Endpoint.newBuilder().setIp("127.0.0.1").setPort(1234).build();
            MethodDescriptor.Marshaller<BasicMeta.Endpoint> codec=ProtoUtils.marshaller(BasicMeta.Endpoint.getDefaultInstance());
            assertEquals(endpoint,codec.parse(codec.stream(endpoint))); // No socket/resolver: literal field only.
            LocalCall call=new LocalCall(endpoint,false);
            ListenableFuture<BasicMeta.Endpoint> response=ClientCalls.futureUnaryCall(call,endpoint);
            assertEquals(endpoint,response.get(2,TimeUnit.SECONDS));assertEquals(endpoint,call.sent);assertTrue(call.requests>0);
            LocalCall pending=new LocalCall(endpoint,true);ListenableFuture<BasicMeta.Endpoint> cancelled=ClientCalls.futureUnaryCall(pending,endpoint);
            assertTrue(cancelled.cancel(true));assertTrue(pending.cancelled);
        }
    }
    /** Real grpc-core in-process transport; no fake ClientCall or external socket. */
    public static class InProcessRpcContracts {
        @Test public void actualInProcessUnaryResponseAndErrorKeepProtoAndStatus() throws Exception {
            try (RpcHarness rpc=new RpcHarness()) {
                BasicMeta.Endpoint response=rpc.call("Echo",CallOptions.DEFAULT).get(2,TimeUnit.SECONDS);
                assertEquals(rpc.request,response);assertEquals(1,rpc.echoes.get());
                try {rpc.call("Error",CallOptions.DEFAULT).get(2,TimeUnit.SECONDS);fail("expected service error");}
                catch(ExecutionException expected){assertEquals(Status.Code.INVALID_ARGUMENT,Status.fromThrowable(expected.getCause()).getCode());}
            }
        }
        @Test public void actualInProcessCancellationReachesServerContextAndShutsDown() throws Exception {
            try (RpcHarness rpc=new RpcHarness()) {
                ListenableFuture<BasicMeta.Endpoint> pending=rpc.call("Hold",CallOptions.DEFAULT);
                assertTrue(rpc.entered.await(2,TimeUnit.SECONDS));assertTrue(pending.cancel(true));
                assertTrue(pending.isCancelled());assertTrue(rpc.cancelled.await(2,TimeUnit.SECONDS));
            }
        }
        @Test public void actualInProcessDeadlineReachesServerContextAndShutsDown() throws Exception {
            try (RpcHarness rpc=new RpcHarness()) {
                ListenableFuture<BasicMeta.Endpoint> pending=rpc.call("Hold",CallOptions.DEFAULT.withDeadlineAfter(400,TimeUnit.MILLISECONDS));
                assertTrue(rpc.entered.await(2,TimeUnit.SECONDS));
                try {pending.get(2,TimeUnit.SECONDS);fail("expected deadline");}
                catch(ExecutionException expected){assertEquals(Status.Code.DEADLINE_EXCEEDED,Status.fromThrowable(expected.getCause()).getCode());}
                assertTrue(rpc.cancelled.await(2,TimeUnit.SECONDS));
            }
        }
    }
    private static final class RpcHarness implements AutoCloseable {
        static final String SERVICE="maintenance.GuavaJava8";
        final BasicMeta.Endpoint request=BasicMeta.Endpoint.newBuilder().setIp("127.0.0.1").setPort(1234).build();
        final AtomicInteger echoes=new AtomicInteger();
        final CountDownLatch entered=new CountDownLatch(1),cancelled=new CountDownLatch(1);
        final Map<String,MethodDescriptor<BasicMeta.Endpoint,BasicMeta.Endpoint>> methods=new HashMap<>();
        final Server server;final ManagedChannel channel;
        RpcHarness() throws Exception {
            for(String name:Arrays.asList("Echo","Error","Hold"))methods.put(name,MethodDescriptor.<BasicMeta.Endpoint,BasicMeta.Endpoint>newBuilder()
                .setType(MethodDescriptor.MethodType.UNARY).setFullMethodName(MethodDescriptor.generateFullMethodName(SERVICE,name))
                .setRequestMarshaller(ProtoUtils.marshaller(BasicMeta.Endpoint.getDefaultInstance()))
                .setResponseMarshaller(ProtoUtils.marshaller(BasicMeta.Endpoint.getDefaultInstance())).build());
            ServerServiceDefinition service=ServerServiceDefinition.builder(SERVICE)
                .addMethod(methods.get("Echo"),io.grpc.stub.ServerCalls.asyncUnaryCall((value,observer)->{echoes.incrementAndGet();observer.onNext(value);observer.onCompleted();}))
                .addMethod(methods.get("Error"),io.grpc.stub.ServerCalls.asyncUnaryCall((value,observer)->observer.onError(Status.INVALID_ARGUMENT.withDescription("inert fixture").asRuntimeException())))
                .addMethod(methods.get("Hold"),io.grpc.stub.ServerCalls.asyncUnaryCall((value,observer)->{
                    Context.current().addListener(context->cancelled.countDown(),MoreExecutors.directExecutor());entered.countDown();
                })).build();
            String name="guava-java8-"+UUID.randomUUID();
            io.grpc.inprocess.InProcessServerBuilder sb=io.grpc.inprocess.InProcessServerBuilder.forName(name).directExecutor().addService(service);
            io.grpc.inprocess.InProcessChannelBuilder cb=io.grpc.inprocess.InProcessChannelBuilder.forName(name).directExecutor();
            // Observe, never modify/disable, upstream stats/tracing module defaults.
            assertEquals(Boolean.TRUE,field(sb,"statsEnabled"));assertEquals(Boolean.TRUE,field(sb,"tracingEnabled"));
            assertEquals(Boolean.TRUE,field(cb,"statsEnabled"));assertEquals(Boolean.TRUE,field(cb,"tracingEnabled"));
            server=sb.build().start();
            try {channel=cb.build();}catch(Throwable failure){server.shutdownNow();assertTrue(server.awaitTermination(2,TimeUnit.SECONDS));throw failure;}
        }
        ListenableFuture<BasicMeta.Endpoint> call(String name,CallOptions options){
            return ClientCalls.futureUnaryCall(channel.newCall(methods.get(name),options),request);
        }
        @Override public void close() throws Exception {
            channel.shutdownNow();server.shutdownNow();
            assertTrue("in-process channel must terminate",channel.awaitTermination(2,TimeUnit.SECONDS));
            assertTrue("in-process server must terminate",server.awaitTermination(2,TimeUnit.SECONDS));
        }
    }
    /** Controlled in-memory transport fixture, not a replacement production gRPC implementation. */
    private static final class LocalCall extends ClientCall<BasicMeta.Endpoint,BasicMeta.Endpoint> {
        final BasicMeta.Endpoint result;final boolean pending;Listener<BasicMeta.Endpoint> listener;BasicMeta.Endpoint sent;int requests;boolean cancelled;
        LocalCall(BasicMeta.Endpoint result,boolean pending){this.result=result;this.pending=pending;}
        @Override public void start(Listener<BasicMeta.Endpoint> listener,Metadata headers){this.listener=listener;}
        @Override public void request(int count){requests+=count;}
        @Override public void cancel(String message,Throwable cause){cancelled=true;}
        @Override public void halfClose(){if(!pending){listener.onMessage(result);listener.onClose(Status.OK,new Metadata());}}
        @Override public void sendMessage(BasicMeta.Endpoint value){sent=value;}
    }
    public static class SerializationBoundaries {
        @Test public void ordinarySelfGeneratedCollectionsRoundTrip() throws Exception {
            for(String name:Arrays.asList("CompactHashSet","CompactHashMap")) {
                Object original=collection(name);assertEquals(original,read(serialize(original).bytes));
            }
            Map<Object,Object> original=new MapMaker().weakKeys().makeMap();original.put("A","one");original.put("B","two");
            Map<?,?> copy=(Map<?,?>)read(serialize(original).bytes);assertEquals(2,copy.size());assertTrue(copy.values().containsAll(Arrays.asList("one","two")));
        }
        @Test public void compactSetDoesNotPreallocateFromFiniteInflatedCount() throws Exception {checkCompact("CompactHashSet","elements");}
        @Test public void compactMapDoesNotPreallocateFromFiniteInflatedCount() throws Exception {checkCompact("CompactHashMap","keys");}
        @Test public void mapMakerDoesNotPreallocateFromFiniteInflatedCount() throws Exception {
            Map<Object,Object> original=new MapMaker().weakKeys().makeMap();original.put("A","one");original.put("B","two");
            Encoded encoded=serialize(original);byte[] bytes=inflate(encoded);Map<?,?> copy=(Map<?,?>)read(bytes);assertEquals(2,copy.size());
            Object[] segments=(Object[])field(copy,"segments");int capacity=0;
            for(Object segment:segments)capacity+=((java.util.concurrent.atomic.AtomicReferenceArray<?>)field(segment,"table")).length();
            System.out.println("MapMaker declared4096, actual2, total table capacity="+capacity);
            assertTrue("finite deserialization capacity must be <=256; actual="+capacity,capacity<=256);
        }
    }
    @SuppressWarnings("unchecked") private static Object collection(String simple) throws Exception {
        Class<?> type=Class.forName("com.google.common.collect."+simple);Method create=type.getDeclaredMethod("create");create.setAccessible(true);Object value=create.invoke(null);
        if(value instanceof Map){((Map<Object,Object>)value).put("A","one");((Map<Object,Object>)value).put("B","two");}
        else {((Set<Object>)value).add("A");((Set<Object>)value).add("B");}return value;
    }
    private static final class Encoded {final byte[] bytes;final int offset;Encoded(byte[] bytes,int offset){this.bytes=bytes;this.offset=offset;}}
    private static Encoded serialize(Object value) throws Exception {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        class RecordingOutput extends ObjectOutputStream {
            int offset=-1;RecordingOutput() throws IOException{super(bytes);}
            @Override public void writeInt(int value) throws IOException {
                flush();super.writeInt(value);flush();
                if(value==2){if(offset!=-1)throw new IOException("ambiguous size fixture");offset=bytes.size()-4;}
            }
        }
        RecordingOutput out=new RecordingOutput();out.writeObject(value);out.close();byte[] data=bytes.toByteArray();
        assertTrue(data.length<4096);assertTrue(out.offset>=0);assertEquals(2,ByteBuffer.wrap(data,out.offset,4).getInt());return new Encoded(data,out.offset);
    }
    private static byte[] inflate(Encoded encoded){byte[] data=encoded.bytes.clone();ByteBuffer.wrap(data,encoded.offset,4).putInt(4096);return data;}
    private static Object read(byte[] bytes) throws Exception {try(ObjectInputStream in=new ObjectInputStream(new ByteArrayInputStream(bytes))){return in.readObject();}}
    private static Object field(Object value,String name) throws Exception {
        for(Class<?> c=value.getClass();c!=null;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.get(value);}catch(NoSuchFieldException ignored){}
        throw new NoSuchFieldException(name);
    }
    private static void checkCompact(String simple,String arrayField) throws Exception {
        byte[] bytes=inflate(serialize(collection(simple)));
        class ObservingInput extends ObjectInputStream {
            int capacity=-1;ObservingInput() throws IOException{super(new ByteArrayInputStream(bytes));enableResolveObject(true);}
            @Override protected Object resolveObject(Object obj) throws IOException {
                if("B".equals(obj))try{
                    Object handles=field(this,"handles");Object[] entries=(Object[])field(handles,"entries");
                    for(Object target:entries)if(target!=null&&target.getClass().getName().equals("com.google.common.collect."+simple)){
                        Object array=field(target,arrayField);if(array!=null)capacity=Array.getLength(array);
                    }
                }catch(Exception e){throw new IOException(e);}return obj;
            }
        }
        try(ObservingInput in=new ObservingInput()) {
            try{in.readObject();fail("inflated count with only2elements must fail closed");}catch(EOFException|OptionalDataException expected){}
            System.out.println(simple+" declared4096, actual2, observed backing capacity="+in.capacity);
            assertTrue("fixture must observe allocated backing array",in.capacity>0);
            assertTrue("finite deserialization capacity must be <=256; actual="+in.capacity,in.capacity<=256);
        }
    }
}
