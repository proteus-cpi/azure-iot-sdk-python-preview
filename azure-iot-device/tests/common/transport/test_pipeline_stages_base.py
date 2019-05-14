# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import logging
import pytest
import functools
from azure.iot.device.common.transport import pipeline_stages_base
from azure.iot.device.common.transport import pipeline_ops_base
from azure.iot.device.common.transport import pipeline_events_base

logging.basicConfig(level=logging.INFO)


def assert_default_attributes(obj):
    assert obj.name is obj.__class__.__name__
    assert obj.next is None
    assert obj.previous is None
    assert obj.pipeline_root is None


# because PipelineStage is abstract, we need something concrete
class PipelineStage(pipeline_stages_base.PipelineStage):
    def _run_op(self, op):
        pass


def Op():
    return pipeline_ops_base.PipelineOperation()


def get_fake_error():
    return BaseException()


@pytest.fixture
def stage(mocker):
    def stage_run_op(self, op):
        if getattr(op, "action", None) is None or op.action == "pass":
            self.complete_op(op)
        elif op.action == "fail":
            raise get_fake_error()
        elif op.action == "pend":
            pass
        else:
            assert False

    first_stage = PipelineStage()
    first_stage.unhandled_error_handler = mocker.Mock()
    first_stage._run_op = functools.partial(stage_run_op, first_stage)
    mocker.spy(first_stage, "_run_op")
    mocker.spy(first_stage, "run_op")

    next_stage = PipelineStage()
    next_stage._run_op = functools.partial(stage_run_op, next_stage)
    mocker.spy(next_stage, "_run_op")
    mocker.spy(next_stage, "run_op")

    first_stage.next = next_stage
    first_stage.pipeline_root = first_stage

    next_stage.previous = first_stage
    next_stage.pipeline_root = first_stage

    return first_stage


@pytest.fixture
def callback(mocker):
    return mocker.Mock()


@pytest.fixture
def op():
    op = Op()
    op.name = "op"
    return op


@pytest.fixture
def op2():
    op = Op()
    op.name = "op2"
    return op


@pytest.fixture
def op3():
    op = Op()
    op.name = "op3"
    return op


@pytest.fixture
def finally_op():
    op = Op()
    op.name = "finally_op"
    return op


@pytest.fixture
def fake_error():
    return get_fake_error()


@pytest.fixture
def event():
    ev = pipeline_events_base.PipelineEvent()
    ev.name = "test event"
    return ev


def assert_callback_succeeded(callback, op):
    assert callback.call_count == 1
    callback_arg = callback.call_args[0][0]
    assert callback_arg == op
    assert op.error is None


def assert_callback_failed(callback, op, error=None):
    assert callback.call_count == 1
    callback_arg = callback.call_args[0][0]
    assert callback_arg == op

    if error:
        assert op.error is error
    else:
        assert op.error is not None


@pytest.mark.describe("PipelineStage initializer")
class TestPipelineStageInitializer(object):
    @pytest.mark.it("Sets name attribute on instantiation")
    @pytest.mark.it("Sets next attribute to None on instantiation")
    @pytest.mark.it("Sets previous attribute to None on instantiation")
    @pytest.mark.it("Sets pipeline_root attribute to None on instantiation")
    def test_initializer(self):
        obj = PipelineStage()
        assert_default_attributes(obj)


@pytest.mark.describe("PipelineStage RunOp function")
class TestPipelineStageRunOp(object):
    @pytest.mark.it("calls _run_op")
    def test_calls_run_op(self, mocker, stage, op):
        stage.run_op(op)
        assert stage._run_op.call_count == 1
        assert stage._run_op.call_args == mocker.call(op)

    @pytest.mark.it("completes the op with error if the op throws")
    def test_completes_with_error_if_op_throws(self, stage, callback, op):
        op.action = "fail"
        op.callback = callback
        stage.run_op(op)
        assert_callback_failed(callback, op)


@pytest.mark.describe("PipelineStage run_ops_serial function")
class TestPipelineStageRunOpsSerial(object):
    @pytest.mark.it("accepts a list of operators and a callback")
    def test_accepts_default_args(self, stage, callback):
        stage.run_ops_serial(Op(), Op(), callback=callback)

    @pytest.mark.it("accepts finally_op as an optional keyword args")
    def test_accepts_finally_op(self, stage, callback):
        stage.run_ops_serial(Op(), Op(), callback=callback, finally_op=Op())

    @pytest.mark.it("throws TypeError for any keyword args besides finally_op and callback")
    def test_throws_for_unknown_keyword_args(self, stage, callback):
        with pytest.raises(TypeError):
            stage.run_ops_serial(Op(), Op(), callback=callback, unknown_arg=Op())

    @pytest.mark.it("requires the callback arg")
    def test_throws_on_missing_callback(self, stage):
        with pytest.raises(TypeError):
            stage.run_ops_serial(Op(), Op())


@pytest.mark.describe("PipelineStage run_ops_serial function with one op and without finally op")
class TestPipelineStageRunOpsSerialOneOpButNoFinallyOp(object):
    @pytest.mark.it("runs the op")
    def test_runs_operation(self, mocker, stage, callback, op):
        stage.run_ops_serial(op, callback=callback)
        assert stage.next._run_op.call_count == 1
        assert stage.next._run_op.call_args == mocker.call(op)

    @pytest.mark.it("calls the callback with the op if the op succeeds")
    @pytest.mark.it("calls the callback with no error if the op succeeds")
    def test_successful_operation(self, stage, callback, op):
        stage.run_ops_serial(op, callback=callback)
        assert_callback_succeeded(callback, op)

    @pytest.mark.it("calls the callback with the op if the op fails")
    @pytest.mark.it("calls the callback with the op error if the op fails")
    def test_failed_operation(self, stage, callback, op):
        op.action = "fail"
        stage.run_ops_serial(op, callback=callback)
        assert_callback_failed(callback, op)

    @pytest.mark.it("protects the callback with a try/except block")
    def test_exception_in_callback(self, stage, mocker, fake_error, op):
        callback = mocker.Mock(side_effect=fake_error)
        stage.run_ops_serial(op, callback=callback)
        assert callback.call_count == 1
        assert callback.call_args == mocker.call(op)
        assert stage.unhandled_error_handler.call_count == 1
        assert stage.unhandled_error_handler.call_args == mocker.call(fake_error)


@pytest.mark.describe("PipelineStage run_ops_serial function with one op and finally op")
class TestPipelineStageRunOpsSerialOneOpAndFinallyOp(object):
    @pytest.mark.it("runs the first op")
    def test_runs_first_op(self, mocker, stage, callback, op, finally_op):
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert stage.next._run_op.call_args_list[0] == mocker.call(op)

    @pytest.mark.it("runs finally_op if the op succeeds")
    def test_runs_finally_op_on_success(self, mocker, stage, callback, op, finally_op):
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert stage.next._run_op.call_args_list[1] == mocker.call(finally_op)

    @pytest.mark.it("runs finally_op if the op fails")
    def test_runs_finally_op_on_op_failure(self, mocker, stage, callback, op, finally_op):
        op.action = "fail"
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert stage.next._run_op.call_args_list[1] == mocker.call(finally_op)

    @pytest.mark.it("calls the callback with the finally_op if op succeeds and finally_op fails")
    @pytest.mark.it(
        "calls the callback with the finally_op error if op succeeds and finally_op fails"
    )
    def test_calls_callback_with_error_if_op_succeeds_and_finally_op_fails(
        self, stage, callback, op, finally_op
    ):
        finally_op.action = "fail"
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert_callback_failed(callback, finally_op, error=finally_op.error)

    @pytest.mark.it("calls the callback with the finally_op if op succeeds and finally_op succeeds")
    @pytest.mark.it("calls the callback with no error if op succeeds and finally_op succeeds")
    def test_callback_with_success_if_op_and_finally_op_succeed(
        self, stage, callback, op, finally_op
    ):
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert_callback_succeeded(callback, finally_op)

    @pytest.mark.it("calls the callback with the finally_op if op fails and finally_op also fails")
    @pytest.mark.it("calls the callback with op error if op fails and finally_op also fails")
    def test_callback_with_error_if_op_and_finally_op_both_fail(
        self, stage, callback, op, finally_op
    ):
        op.action = "fail"
        finally_op.action = "fail"
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert_callback_failed(callback, finally_op, error=op.error)

    @pytest.mark.it("calls the callback with the finally_op if op fails and finally_op succeeds")
    @pytest.mark.it("calls the callback with op error if op fails and finally_op succeeds")
    def test_callback_with_error_if_op_fails_and_finally_op_succeeds(
        self, stage, callback, op, finally_op
    ):
        op.action = "fail"
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert_callback_failed(callback, finally_op, error=op.error)

    @pytest.mark.it("protects the callback with a try/except block")
    def test_exception_in_callback(self, stage, op, finally_op, fake_error, mocker):
        callback = mocker.Mock(side_effect=fake_error)
        stage.run_ops_serial(op, finally_op=finally_op, callback=callback)
        assert callback.call_count == 1
        assert callback.call_args == mocker.call(finally_op)
        assert stage.unhandled_error_handler.call_count == 1
        assert stage.unhandled_error_handler.call_args == mocker.call(fake_error)


@pytest.mark.describe("PipelineStage run_ops_serial function with three ops and without finally op")
class TestPipelineStageRunOpsSerialThreeOpsButNoFinallyOp(object):
    @pytest.mark.it("runs the first op")
    def test_runs_first_op(self, mocker, stage, op, op2, op3, callback):
        op.action = "pend"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert stage.next._run_op.call_count == 1
        assert stage.next._run_op.call_args == mocker.call(op)

    @pytest.mark.it("does not call the second or third op if the first op fails")
    def test_does_not_call_second_or_third_op_if_first_op_fails(
        self, mocker, stage, op, op2, op3, callback
    ):
        op.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert stage.next._run_op.call_count == 1
        assert stage.next._run_op.call_args == mocker.call(op)

    @pytest.mark.it("calls the callback with the first op if the first op fails")
    @pytest.mark.it("calls the callback with the first op error if the first op fails")
    def test_calls_callback_when_first_op_fails(self, stage, op, op2, op3, callback):
        op.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert_callback_failed(callback, op)

    @pytest.mark.it("protects the callback with a try/except block")
    def test_exception_in_callback(self, stage, op, op2, op3, fake_error, mocker):
        callback = mocker.Mock(side_effect=fake_error)
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert callback.call_count == 1
        assert callback.call_args == mocker.call(op3)
        assert stage.unhandled_error_handler.call_count == 1
        assert stage.unhandled_error_handler.call_args == mocker.call(fake_error)

    @pytest.mark.it("runs the second op only after the first op succeeds")
    def test_runs_second_op_after_first_op_succceeds(self, mocker, stage, op, op2, op3, callback):
        op.action = "pend"
        op2.action = "pend"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert stage.next._run_op.call_count == 1
        assert stage.next._run_op.call_args == mocker.call(op)
        stage.next.complete_op(op)
        assert stage.next._run_op.call_count == 2
        assert stage.next._run_op.call_args_list[1] == mocker.call(op2)

    @pytest.mark.it("does not run the third op after the second op fails")
    def test_does_not_run_third_op_if_second_op_fails(self, mocker, stage, op, op2, op3, callback):
        op2.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert stage.next._run_op.call_count == 2
        assert stage.next._run_op.call_args_list[0] == mocker.call(op)
        assert stage.next._run_op.call_args_list[1] == mocker.call(op2)

    @pytest.mark.it("calls the callback with the second op if the second op fails")
    @pytest.mark.it("calls the callback with the second op error if the second op fails")
    def test_calls_callback_when_second_op_fails(self, stage, op, op2, op3, callback):
        op2.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert_callback_failed(callback, op2)

    @pytest.mark.it("calls the third op only after the second op succeeds")
    def test_calls_third_op_after_second_op_succeeds(self, mocker, stage, op, op2, op3, callback):
        op2.action = "pend"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert stage.next._run_op.call_count == 2
        assert stage.next._run_op.call_args_list[0] == mocker.call(op)
        assert stage.next._run_op.call_args_list[1] == mocker.call(op2)
        stage.next.complete_op(op2)
        assert stage.next._run_op.call_count == 3
        assert stage.next._run_op.call_args_list[2] == mocker.call(op3)

    @pytest.mark.it("calls the callback with the third op if the third op succeeds")
    @pytest.mark.it("calls the callback with success if the third op succeeds")
    def test_calls_callback_with_third_op_succeeds(self, stage, op, op2, op3, callback):
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert_callback_succeeded(callback, op3)

    @pytest.mark.it("calls the callback with the third op if the third op fails")
    @pytest.mark.it("calls the callback with the third op error if the third op fails")
    def test_calls_callback_when_third_op_fails(self, stage, op, op2, op3, callback):
        op3.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback)
        assert_callback_failed(callback, op3)


@pytest.mark.describe("PipelineStage run_ops_serial function with three ops and finally op")
class TestPipelineStageRunOpsSerialThreeOpsAndFinallyOp(object):
    @pytest.mark.it("runs the first op")
    def test_runs_first_op(self, mocker, stage, op, op2, op3, finally_op, callback):
        op.action = "pend"
        stage.run_ops_serial(op, op2, op3, finally_op=finally_op, callback=callback)
        assert stage.next._run_op.call_count == 1
        assert stage.next._run_op.call_args == mocker.call(op)

    @pytest.mark.it("does not call the second or third op if the first op fails")
    @pytest.mark.it("runs the finally op if the first op fails")
    def test_runs_finally_op_if_first_op_fails(
        self, mocker, stage, op, op2, op3, finally_op, callback
    ):
        op.action = "fail"
        stage.run_ops_serial(op, op2, op3, finally_op=finally_op, callback=callback)
        assert stage.next._run_op.call_count == 2
        assert stage.next._run_op.call_args_list[0] == mocker.call(op)
        assert stage.next._run_op.call_args_list[1] == mocker.call(finally_op)

    @pytest.mark.it(
        "calls the callback with the finally_op if the first op fails and finally_op succeeds"
    )
    @pytest.mark.it(
        "calls the callback with first_op error if the first op fails and finally_op succeeds"
    )
    def test_calls_callback_with_error_when_first_op_fails_and_finally_op_succeeds(
        self, stage, op, op2, op3, finally_op, callback
    ):
        op.action = "fail"
        stage.run_ops_serial(op, op2, op3, finally_op=finally_op, callback=callback)
        assert_callback_failed(callback, finally_op, error=op.error)

    @pytest.mark.it(
        "calls the callback with the finally_op if the first op fails and finally_op also fails"
    )
    @pytest.mark.it(
        "calls the callback with first_op error if the first op fails and finally_op also fails"
    )
    def test_calls_callbacK_with_error_when_first_op_and_finally_op_both_fail(
        self, stage, op, op2, op3, finally_op, callback
    ):
        op.action = "fail"
        finally_op.action = "fail"
        stage.run_ops_serial(op, op2, op3, finally_op=finally_op, callback=callback)
        assert_callback_failed(callback, finally_op, error=finally_op.error)

    @pytest.mark.it("protects the callback with a try/except block")
    def test_exception_in_callback(self, stage, op, op2, op3, finally_op, fake_error, mocker):
        callback = mocker.Mock(side_effect=fake_error)
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert stage.unhandled_error_handler.call_count == 1
        assert stage.unhandled_error_handler.call_args == mocker.call(fake_error)

    @pytest.mark.it("runs the second op only after the first op succeeds")
    def test_runs_second_op(self, mocker, stage, op, op2, op3, finally_op, callback):
        op.action = "pend"
        op2.action = "pend"
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert stage.next._run_op.call_count == 1
        assert stage.next._run_op.call_args == mocker.call(op)
        stage.next.complete_op(op)
        assert stage.next._run_op.call_args_list[1] == mocker.call(op2)

    @pytest.mark.it("does not run the third op after the second op fails")
    @pytest.mark.it("runs finally_op if the second op fails")
    def test_runs_finally_op_when_second_op_fails(
        self, mocker, stage, op, op2, op3, finally_op, callback
    ):
        op2.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert stage.next._run_op.call_count == 3
        assert stage.next._run_op.call_args_list[0] == mocker.call(op)
        assert stage.next._run_op.call_args_list[1] == mocker.call(op2)
        assert stage.next._run_op.call_args_list[2] == mocker.call(finally_op)

    @pytest.mark.it(
        "calls the callback with finally_op if the second op fails and finally_op succeeds"
    )
    @pytest.mark.it(
        "calls the callback with second_op error if the second op fails and finally_op succeeds"
    )
    def test_calls_callback_with_error_when_second_op_fails_and_finally_op_succeeds(
        self, stage, op, op2, op3, finally_op, callback
    ):
        op2.action = "fail"
        stage.run_ops_serial(op, op2, op3, finally_op=finally_op, callback=callback)
        assert_callback_failed(callback, finally_op, error=op.error)

    @pytest.mark.it(
        "calls the callback with the finally_op if the second op fails and finally_op also fails"
    )
    @pytest.mark.it(
        "calls the callback with second_op error if the second op fails and finally_op also fails"
    )
    def test_calls_callback_with_error_when_second_op_and_finally_op_both_fail(
        self, stage, op, op2, op3, finally_op, callback
    ):
        op2.action = "fail"
        finally_op.action = "fail"
        stage.run_ops_serial(op, op2, op3, finally_op=finally_op, callback=callback)
        assert_callback_failed(callback, finally_op, error=finally_op.error)
        pass

    @pytest.mark.it("runs the third op only after the second op succeeds")
    def test_runs_third_op_after_second_op_succeeds(
        self, mocker, stage, op, op2, op3, finally_op, callback
    ):
        op2.action = "pend"
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert stage.next._run_op.call_count == 2
        assert stage.next._run_op.call_args_list[0] == mocker.call(op)
        assert stage.next._run_op.call_args_list[1] == mocker.call(op2)
        stage.next.complete_op(op2)
        assert stage.next._run_op.call_count == 4
        assert stage.next._run_op.call_args_list[2] == mocker.call(op3)
        assert stage.next._run_op.call_args_list[3] == mocker.call(finally_op)

    @pytest.mark.it("runs finally_op if the third op fails")
    def test_runs_finally_op_if_third_op_fails(
        self, mocker, stage, op, op2, op3, finally_op, callback
    ):
        op3.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert stage.next._run_op.call_count == 4
        assert stage.next._run_op.call_args_list[3] == mocker.call(finally_op)

    @pytest.mark.it("runs finally_op if the third op succeeds")
    def test_runs_finally_op_if_third_op_succeeds(
        self, mocker, stage, op, op2, op3, finally_op, callback
    ):
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert stage.next._run_op.call_count == 4
        assert stage.next._run_op.call_args_list[3] == mocker.call(finally_op)

    @pytest.mark.it(
        "calls the callback with no the finally_op if the third op succeeds and finally_op also succeeds"
    )
    @pytest.mark.it(
        "calls the callback with no error if the third op succeeds and finally_op also succeeds"
    )
    def test_calls_callback_with_no_error_if_third_op_and_finally_op_both_succeed(
        self, stage, op, op2, op3, finally_op, callback
    ):
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert_callback_succeeded(callback, finally_op)

    @pytest.mark.it(
        "calls the callback with the finally_op if the third op succeeds and finally_op fails"
    )
    @pytest.mark.it(
        "calls the callback with finally_op error if the third op succeeds and finally_op fails"
    )
    def test_calls_callback_with_error_if_third_op_succeeds_and_finally_op_fails(
        self, stage, op, op2, op3, finally_op, callback
    ):
        finally_op.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert_callback_failed(callback, finally_op, error=finally_op.error)

    @pytest.mark.it(
        "calls the callback with the finally_op if the third op fails and finally_op succeeds"
    )
    @pytest.mark.it(
        "calls the callback with the third op error if the third op fails and finally_op succeeds"
    )
    def test_calls_callback_with_error_if_the_third_op_fails_and_finally_op_succeeds(
        self, stage, op, op2, op3, finally_op, callback
    ):
        op3.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert_callback_failed(callback, finally_op, error=op3.error)

    @pytest.mark.it(
        "calls the callback with the finally_op if the third op fails and finally_op also fails"
    )
    @pytest.mark.it(
        "calls the callback with third op error if the third op fails and finally_op also fails"
    )
    def test_calls_callback_with_error_if_third_op_and_finally_op_both_fail(
        self, stage, op, op2, op3, finally_op, callback
    ):
        op3.action = "fail"
        finally_op.action = "fail"
        stage.run_ops_serial(op, op2, op3, callback=callback, finally_op=finally_op)
        assert_callback_failed(callback, finally_op, error=op3.error)


@pytest.mark.describe("PipelineStage handle_pipeline_event function")
class TestPipelineStageHandlePipelineEvent(object):
    @pytest.mark.it("calls _handle_pipeline_event")
    def test_calls_private_handle_pipeline_event(self, stage, event, mocker):
        stage._handle_pipeline_event = mocker.Mock()
        stage.handle_pipeline_event(event)
        assert stage._handle_pipeline_event.call_count == 1
        assert stage._handle_pipeline_event.call_args == mocker.call(event)

    @pytest.mark.it("protects _handle_pipeline_event with a try/except block")
    def test_exception_in_provate_handle_pipeline_event(self, stage, event, fake_error, mocker):
        stage._handle_pipeline_event = mocker.Mock(side_effect=fake_error)
        stage.handle_pipeline_event(event)
        assert stage.unhandled_error_handler.call_count == 1
        assert stage.unhandled_error_handler.call_args == mocker.call(fake_error)


@pytest.mark.describe("PipelineStage _handle_pipeline_event function")
class TestPipelineStageHandlePrivatePipelineEvent(object):
    @pytest.mark.it("calls the handle_pipeline_event function in the previous stage")
    def test_calls_previous_stage_handle_pipeline_event(self, stage, event, mocker):
        stage.handle_pipeline_event = mocker.Mock()
        stage.next._handle_pipeline_event(event)
        assert stage.handle_pipeline_event.call_count == 1
        assert stage.handle_pipeline_event.call_args == mocker.call(event)

    @pytest.mark.it("calls the unhandled error handler if there is no previous stage")
    def test_error_if_no_previous_stage(self, stage, event):
        stage.previous = None
        stage.unhandled_error_handler.assert_not_called()
        stage._handle_pipeline_event(event)
        assert stage.unhandled_error_handler.call_count == 1


@pytest.mark.describe("PipelineStage continue_op function")
class TestPipelineStageContinueOp(object):
    @pytest.mark.it("completes the op without continuing if the op has an error")
    def test_completes_op_with_error(self, mocker, stage, op, fake_error, callback):
        op.error = fake_error
        op.callback = callback
        stage.continue_op(op)
        assert callback.call_count == 1
        assert callback.call_args == mocker.call(op)
        assert stage.next.run_op.call_count == 0

    @pytest.mark.it("fails the op if there is no next stage")
    def test_fails_op_when_no_next_stage(self, stage, op, callback):
        op.callback = callback
        stage.next = None
        stage.continue_op(op)
        assert_callback_failed(callback, op)
        pass

    @pytest.mark.it("passes the op to the next stage if no error")
    def test_passes_op_to_next_stage(self, mocker, stage, op, callback):
        stage.continue_op(op)
        assert stage.next.run_op.call_count == 1
        assert stage.next.run_op.call_args == mocker.call(op)


@pytest.mark.describe("PipelineStage complete_op function")
class TestPipelineStageCompleteOp(object):
    @pytest.mark.it("calls the op callback on success")
    def test_calls_callback_on_success(self, stage, op, callback):
        op.callback = callback
        stage.complete_op(op)
        assert_callback_succeeded(callback, op)

    @pytest.mark.it("calls the op callback on failure")
    def test_calls_callback_on_error(self, stage, op, callback, fake_error):
        op.error = fake_error
        op.callback = callback
        stage.complete_op(op)
        assert_callback_failed(callback, op, fake_error)

    @pytest.mark.it("protects the op callback with a try/except handler")
    def test_exception_in_callback(self, stage, op, fake_error, mocker):
        op.callback = mocker.Mock(side_effect=fake_error)
        stage.complete_op(op)
        assert op.callback.call_count == 1
        assert op.callback.call_args == mocker.call(op)
        assert stage.unhandled_error_handler.call_count == 1
        assert stage.unhandled_error_handler.call_args == mocker.call(fake_error)


@pytest.mark.describe("PipelineStage continue_with_different_op function")
class TestPipelineStageContineWithDifferntOp(object):
    @pytest.mark.it("does not continue running the original op")
    @pytest.mark.it("runs the new op")
    def test_runs_new_op(self, mocker, stage, op):
        new_op = Op()
        stage.continue_with_different_op(original_op=op, new_op=new_op)
        assert stage.next.run_op.call_count == 1
        assert stage.next.run_op.call_args == mocker.call(new_op)

    @pytest.mark.it("completes the original op after the new op completes")
    def test_completes_original_op_after_new_op_completes(self, stage, op, callback):
        op.callback = callback
        new_op = Op()
        new_op.action = "pend"

        stage.continue_with_different_op(original_op=op, new_op=new_op)
        assert callback.call_count == 0  # because new_op is pending

        stage.next.complete_op(new_op)
        assert_callback_succeeded(callback, op)

    @pytest.mark.it("returns the new op failure in the original op if new op fails")
    def test_returns_new_op_failure_in_original_op(self, stage, op, callback):
        op.callback = callback
        new_op = Op()
        new_op.action = "fail"
        stage.continue_with_different_op(original_op=op, new_op=new_op)
        assert_callback_failed(callback, op, new_op.error)
